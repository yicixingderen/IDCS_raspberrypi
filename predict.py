import os
import sys

import torch
import torchvision.transforms as transforms

from mobile_shuffle import mobilenet_shuffle


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
TARGET_IMAGE_SIZE = (224, 224)

_CLASSES = {
    '0': '开裂',
    '1': '内含物',
    '2': '斑块',
    '3': '点蚀表面',
    '4': '轧制氧化皮',
    '5': '划痕',
}

_TRANSFORM = transforms.Compose([
    transforms.Resize(TARGET_IMAGE_SIZE, interpolation=transforms.InterpolationMode.BILINEAR),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
])

_MODEL = None
_MODEL_PATH = None
_MODEL_MTIME = None


def _resolve_model_path():
    candidates = []

    if getattr(sys, 'frozen', False):
        frozen_base = getattr(sys, '_MEIPASS', BASE_DIR)
        candidates.append(os.path.join(frozen_base, 'net_070.pth'))
        candidates.append(os.path.join(os.path.dirname(sys.executable), 'net_070.pth'))

    candidates.append(os.path.join(BASE_DIR, 'net_070.pth'))
    candidates.append(os.path.join(BASE_DIR, '..', 'net_070.pth'))

    for model_path in candidates:
        if os.path.exists(model_path):
            return model_path

    raise FileNotFoundError('未找到模型权重文件 net_070.pth，请确认文件与程序位于同一目录。')


def _safe_load_state_dict(model_weight_pth):
    # Try low-memory loading first for resource-limited boards.
    load_options = [
        {'weights_only': True, 'mmap': True},
        {'weights_only': True},
        {'mmap': True},
        {},
    ]

    for option in load_options:
        try:
            return torch.load(model_weight_pth, map_location=device, **option)
        except TypeError:
            continue

    return torch.load(model_weight_pth, map_location=device)


def _load_model_once():
    global _MODEL, _MODEL_PATH, _MODEL_MTIME

    model_weight_pth = _resolve_model_path()
    model_mtime = os.path.getmtime(model_weight_pth)

    if (
        _MODEL is not None
        and _MODEL_PATH == model_weight_pth
        and _MODEL_MTIME == model_mtime
    ):
        return _MODEL

    state_dict = _safe_load_state_dict(model_weight_pth)

    num_classes = len(_CLASSES)
    classifier_weight = state_dict.get('classifier.weight') if isinstance(state_dict, dict) else None
    if classifier_weight is not None and hasattr(classifier_weight, 'shape'):
        weight_num_classes = int(classifier_weight.shape[0])
        if weight_num_classes != num_classes:
            raise RuntimeError(
                f'模型分类头输出通道不匹配：权重通道={weight_num_classes}，期望通道={num_classes}。'
                '请使用6类重新训练并导出权重。'
            )

    model = mobilenet_shuffle(num_classes=num_classes).to(device)
    model.load_state_dict(state_dict)
    model.eval()

    _MODEL = model
    _MODEL_PATH = model_weight_pth
    _MODEL_MTIME = model_mtime
    return _MODEL


def predict_(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img = _TRANSFORM(img)
    img = torch.unsqueeze(img, dim=0).to(device)

    model = _load_model_once()

    with torch.inference_mode():
        output = torch.squeeze(model(img))
        if output.numel() != len(_CLASSES):
            raise RuntimeError(f'模型输出维度异常：{output.numel()}，期望维度：{len(_CLASSES)}')

        predict = torch.softmax(output, dim=0)
        predict_cla = int(torch.argmax(predict).cpu().item())

    return _CLASSES[str(predict_cla)], float(predict[predict_cla].item())
