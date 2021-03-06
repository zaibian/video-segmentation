import itertools
import random

import cv2
import numpy as np

from cityscapes_generator import CityscapesGenerator
from base_generator import threadsafe_generator


class CityscapesGeneratorForICNet(CityscapesGenerator):
    gt_sub = [4, 8, 16]

    @threadsafe_generator
    def flow(self, type, batch_size, target_size):
        """
        :param type: one of [train,val,test]
        :param batch_size:
        :param target_size:
        :return:
        """
        if not self._files_loaded:
            raise Exception('Files weren\'t loaded first!')

        zipped = itertools.cycle(self._data[type])
        i = 0

        while True:
            X = [[]] * 1

            Y = []
            Y2 = []
            Y3 = []

            for _ in range(batch_size):
                img_path, label_path = next(zipped)
                apply_flip = self.flip_enabled and random.randint(0, 1)

                img = self._prep_img(type, img_path, target_size, apply_flip)
                img = self.normalize(img, target_size)

                X[0].append(img)

                seg_img = self._prep_gt(type, label_path, target_size, apply_flip)

                seg_tensor = self.one_hot_encoding(seg_img, tuple(a // 4 for a in target_size))  # target_size)
                Y.append(seg_tensor)

                seg_tensor2 = self.one_hot_encoding(seg_img, tuple(a // 8 for a in target_size))
                Y2.append(seg_tensor2)

                seg_tensor3 = self.one_hot_encoding(seg_img, tuple(a // 16 for a in target_size))
                Y3.append(seg_tensor3)

            i += 1

            x = [np.asarray(j) for j in X]
            y = [np.array(Y), np.array(Y2), np.array(Y3)]
            yield x, y


if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path

        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    else:
        __package__ = ''

    import config

    datagen = CityscapesGeneratorForICNet(config.data_path(), flip_enabled=True)

    batch_size = 1
    # target_size = 288, 480
    target_size = 256, 512
    # target_size = 1024, 2048  # orig size

    for imgBatch, labelBatch in datagen.flow('train', batch_size, target_size):
        print(len(imgBatch))

        img = imgBatch[0][0]
        label = labelBatch[0][0]

        colored_class_image = datagen.one_hot_to_bgr(label, tuple(a // 4 for a in target_size), datagen.n_classes, datagen.labels)

        cv2.imshow("normalized", img)
        cv2.imshow("gt", colored_class_image)
        cv2.waitKey()
