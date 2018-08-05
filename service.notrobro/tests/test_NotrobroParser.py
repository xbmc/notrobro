# -*- coding: utf-8 -*-
#

import pytest
import os
import sys
import mock
import logging

from resources.lib.NotrobroParser import NotrobroParser

logger = mock.Mock()
dir_path = os.path.dirname(os.path.realpath(__file__))

def test_parser():
    parser = NotrobroParser(os.path.join(dir_path, 'test_1.edl'), logger)
    intro_start_time, intro_end_time = parser.intro
    outro_start_time, outro_end_time = parser.outro  
    assert intro_start_time == 109.067
    assert intro_end_time == 176.176
    assert outro_start_time == 1123.809
    assert outro_end_time == 1279.715
    assert logger.assert_not_called

def test_parser_file_not_found():
    NotrobroParser(os.path.join(dir_path, 'does_not_exist.edl'), logger)
    assert logger.assert_called_once
