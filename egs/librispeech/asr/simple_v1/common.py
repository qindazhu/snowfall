#!/usr/bin/env python3

# Copyright 2019-2020 Mobvoi AI Lab, Beijing, China (author: Fangjun Kuang)
# Apache 2.0

import os
from datetime import datetime
import logging
import numpy as np
import torch


def setup_logger(log_filename, log_level='info'):
    now = datetime.now()
    date_time = now.strftime('%Y-%m-%d-%H-%M-%S')
    log_filename = '{}-{}'.format(log_filename, date_time)
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    formatter = '%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
    if log_level == 'debug':
        level = logging.DEBUG
    elif log_level == 'info':
        level = logging.INFO
    elif log_level == 'warning':
        level = logging.WARNING
    logging.basicConfig(filename=log_filename,
                        format=formatter,
                        level=level,
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(formatter))
    logging.getLogger('').addHandler(console)


def load_checkpoint(filename, model):
    logging.info('load checkpoint from {}'.format(filename))

    checkpoint = torch.load(filename, map_location='cpu')

    keys = ['state_dict', 'epoch', 'learning_rate', 'objf']
    for k in keys:
        assert k in checkpoint

    if not list(model.state_dict().keys())[0].startswith('module.') \
            and list(checkpoint['state_dict'])[0].startswith('module.'):
        # the checkpoint was saved by DDP
        logging.info('load checkpoint from DDP')
        dst_state_dict = model.state_dict()
        src_state_dict = checkpoint['state_dict']
        for key in dst_state_dict.keys():
            src_key = '{}.{}'.format('module', key)
            dst_state_dict[key] = src_state_dict.pop(src_key)
        assert len(src_state_dict) == 0
        model.load_state_dict(dst_state_dict)
    else:
        model.load_state_dict(checkpoint['state_dict'])

    epoch = checkpoint['epoch']
    learning_rate = checkpoint['learning_rate']
    objf = checkpoint['objf']

    return epoch, learning_rate, objf


def save_checkpoint(filename, model, epoch, learning_rate, objf, local_rank=0):
    if local_rank != None and local_rank != 0:
        return

    logging.info('Save checkpoint to {filename}: epoch={epoch}, '
                 'learning_rate={learning_rate}, objf={objf}'.format(
                     filename=filename,
                     epoch=epoch,
                     learning_rate=learning_rate,
                     objf=objf))
    checkpoint = {
        'state_dict': model.state_dict(),
        'epoch': epoch,
        'learning_rate': learning_rate,
        'objf': objf
    }
    torch.save(checkpoint, filename)


def save_training_info(filename,
                       model_path,
                       current_epoch,
                       learning_rate,
                       objf,
                       best_objf,
                       best_epoch,
                       local_rank=0):
    if local_rank != None and local_rank != 0:
        return

    with open(filename, 'w') as f:
        f.write('model_path: {}\n'.format(model_path))
        f.write('epoch: {}\n'.format(current_epoch))
        f.write('learning rate: {}\n'.format(learning_rate))
        f.write('objf: {}\n'.format(objf))
        f.write('best objf: {}\n'.format(best_objf))
        f.write('best epoch: {}\n'.format(best_epoch))

    logging.info('write training info to {}'.format(filename))
