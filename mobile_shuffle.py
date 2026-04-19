import math

import torch
import torch.nn as nn

from epsanet import PSAModule


def _act_layer(use_hs=False):
    return nn.Hardswish(inplace=True) if use_hs else nn.ReLU6(inplace=True)


def conv_bn(inp, oup, stride, use_hs=False):
    return nn.Sequential(
        nn.Conv2d(inp, oup, 3, stride, 1, bias=False),
        nn.BatchNorm2d(oup),
        _act_layer(use_hs),
    )


def conv_1x1_bn(inp, oup, use_hs=False):
    return nn.Sequential(
        nn.Conv2d(inp, oup, 1, 1, 0, bias=False),
        nn.BatchNorm2d(oup),
        _act_layer(use_hs),
    )


def conv_5x5(num_channels, use_hs=False):
    return nn.Sequential(
        nn.Conv2d(num_channels, num_channels, 3, padding=3 // 2, bias=False),
        nn.BatchNorm2d(num_channels),
        _act_layer(use_hs),
    )


def make_divisible(x, divisible_by=8):
    import numpy as np

    return int(np.ceil(x * 1.0 / divisible_by) * divisible_by)


def channel_shuffle(x, groups):
    batchsize, num_channels, height, width = x.data.size()
    channels_per_group = num_channels // groups

    x = x.view(batchsize, groups, channels_per_group, height, width)
    x = torch.transpose(x, 1, 2).contiguous()
    x = x.reshape(batchsize, -1, height, width)
    return x


class NASDepthwiseMix(nn.Module):
    def __init__(self, channels, stride=1, kernel_candidates=(3, 5), use_hs=False):
        super(NASDepthwiseMix, self).__init__()
        self.branches = nn.ModuleList()
        for kernel_size in kernel_candidates:
            padding = kernel_size // 2
            self.branches.append(
                nn.Sequential(
                    nn.Conv2d(channels, channels, kernel_size, stride, padding, groups=channels, bias=False),
                    nn.BatchNorm2d(channels),
                )
            )
        self.alpha = nn.Parameter(torch.zeros(len(kernel_candidates)))
        self.act = _act_layer(use_hs)

    def forward(self, x):
        weights = torch.softmax(self.alpha, dim=0)
        out = None
        for w, branch in zip(weights, self.branches):
            branch_out = w * branch(x)
            out = branch_out if out is None else out + branch_out
        return self.act(out)


class InvertedResidual(nn.Module):
    def __init__(
        self,
        inp,
        oup,
        stride,
        expand_ratio,
        groups=2,
        use_hs=False,
        use_nas_kernel_mix=False,
        nas_kernel_candidates=(3, 5),
    ):
        super(InvertedResidual, self).__init__()
        self.stride = stride
        assert stride in [1, 2]

        hidden_dim = int(inp * expand_ratio)
        self.use_res_connect = self.stride == 1 and inp == oup

        self.conv5x5 = conv_5x5(oup, use_hs=use_hs)
        self.groups = groups

        if use_nas_kernel_mix:
            depthwise = NASDepthwiseMix(
                hidden_dim,
                stride=stride,
                kernel_candidates=nas_kernel_candidates,
                use_hs=use_hs,
            )
        else:
            depthwise = nn.Sequential(
                nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False),
                nn.BatchNorm2d(hidden_dim),
                _act_layer(use_hs),
            )

        if expand_ratio == 1:
            self.conv = nn.Sequential(
                depthwise,
                nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False),
                nn.BatchNorm2d(oup),
            )
        else:
            self.conv = nn.Sequential(
                nn.Conv2d(inp, hidden_dim, 1, 1, 0, bias=False),
                nn.BatchNorm2d(hidden_dim),
                _act_layer(use_hs),
                depthwise,
                nn.Conv2d(hidden_dim, oup, 1, 1, 0, bias=False),
                nn.BatchNorm2d(oup),
            )

    def forward(self, x):
        if self.use_res_connect:
            out = self.conv(x)
            out = channel_shuffle(out, groups=self.groups)
            out = self.conv5x5(out)
            return x + out
        return self.conv(x)


class MobileNet_shuffle(nn.Module):
    def __init__(self, num_classes=6, input_size=224, width_mult=1.0, use_hs=True, use_nas_kernel_mix=True):
        super(MobileNet_shuffle, self).__init__()
        block = InvertedResidual
        input_channel = 32
        last_channel = 1280
        interverted_residual_setting = [
            [1, 16, 1, 1],
            [6, 24, 2, 2],
            [6, 32, 3, 2],
            [6, 64, 4, 2],
            [6, 96, 3, 1],
            [6, 160, 3, 2],
            [6, 320, 1, 1],
        ]

        self.epsa = PSAModule(last_channel, last_channel, stride=1, conv_kernels=[3, 5, 7, 9], conv_groups=[1, 2, 2, 2])
        assert input_size % 32 == 0
        self.last_channel = make_divisible(last_channel * width_mult) if width_mult > 1.0 else last_channel
        self.features = [conv_bn(3, input_channel, 2, use_hs=use_hs)]

        for t, c, n, s in interverted_residual_setting:
            output_channel = make_divisible(c * width_mult) if t > 1 else c
            stage_use_hs = use_hs and c >= 64
            stage_nas_mix = use_nas_kernel_mix and t > 1
            stage_kernel_hint = 5 if c >= 96 else 3
            candidates = tuple(sorted(set([3, stage_kernel_hint])))

            for i in range(n):
                stride = s if i == 0 else 1
                self.features.append(
                    block(
                        input_channel,
                        output_channel,
                        stride,
                        expand_ratio=t,
                        use_hs=stage_use_hs,
                        use_nas_kernel_mix=stage_nas_mix,
                        nas_kernel_candidates=candidates,
                    )
                )
                input_channel = output_channel

        self.features.append(conv_1x1_bn(input_channel, self.last_channel, use_hs=use_hs))
        self.features = nn.Sequential(*self.features)
        self.classifier = nn.Linear(self.last_channel, num_classes)

        self._initialize_weights()

    def forward(self, x):
        x = self.features(x)
        x = self.epsa(x)
        x = x.mean(3).mean(2)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2.0 / n))
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                n = m.weight.size(1)
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()


def mobilenet_shuffle(pretrained=False, num_classes=6, use_hs=True, use_nas_kernel_mix=True):
    model = MobileNet_shuffle(
        width_mult=1,
        num_classes=num_classes,
        use_hs=use_hs,
        use_nas_kernel_mix=use_nas_kernel_mix,
    )
    if pretrained:
        try:
            from torch.hub import load_state_dict_from_url
        except ImportError:
            from torch.utils.model_zoo import load_url as load_state_dict_from_url

        state_dict = load_state_dict_from_url(
            "https://www.dropbox.com/s/47tyzpofuuyyv1b/mobilenetv2_1.0-f2a8633.pth.tar?dl=1",
            progress=True,
        )
        if isinstance(state_dict, dict) and "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]
        model.load_state_dict(state_dict, strict=False)
    return model
