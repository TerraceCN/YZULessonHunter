# -*- coding: utf-8 -*-
from io import BytesIO

import numpy as np
from PIL import Image
from onnxruntime import InferenceSession

characters = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789abdefghjmnqrtwxy"

model = InferenceSession('urp.onnx')


def decaptcha(content):
    captcha = np.array([np.array(Image.open(BytesIO(content)))]).astype(np.float32)
    result = model.run([], {'captcha': captcha})
    y = np.argmax(np.array(result), axis=2)[:,0]
    return "".join([characters[x] for x in y])
