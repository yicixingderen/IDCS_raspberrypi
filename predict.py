import os
import sys

import torch
import torchvision.transforms as transforms

from mobile_shuffle import mobilenet_shuffle


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
TARGET_IMAGE_SIZE = (224, 224)

_CLASSES = {
    '0': '精轧辊印',
    '1': '夹渣',
    '2': '铁皮灰',
    '3': '板道系氧化铁皮',
    '4': '温度系氧化铁皮',
    '5': '红铁皮',
    '6': '表面划痕',
}

_TRANSFORM = transforms.Compose([
    transforms.Resize(TARGET_IMAGE_SIZE, interpolation=transforms.InterpolationMode.BILINEAR),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
])

_MODEL = None


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
    global _MODEL

    if _MODEL is not None:
        return _MODEL

    model = mobilenet_shuffle().to(device)
    model_weight_pth = _resolve_model_path()
    state_dict = _safe_load_state_dict(model_weight_pth)
    model.load_state_dict(state_dict)
    model.eval()
    _MODEL = model
    return _MODEL


def predict_(img):
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img = _TRANSFORM(img)
    img = torch.unsqueeze(img, dim=0).to(device)

    model = _load_model_once()

    with torch.inference_mode():
        output = torch.squeeze(model(img))
        predict = torch.softmax(output, dim=0)
        predict_cla = torch.argmax(predict).cpu().numpy()

    return _CLASSES[str(predict_cla)], predict[predict_cla].item()
