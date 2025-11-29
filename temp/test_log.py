#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('modules')

from modules.log import log
import logging

def test_function():
    """测试函数"""
    log("这是来自test_function的测试日志", logging.INFO)

def another_test():
    """另一个测试函数"""
    log("这是来自another_test的测试日志", logging.WARNING)

if __name__ == "__main__":
    log("开始测试日志功能", logging.INFO)
    test_function()
    another_test()
    log("测试完成", logging.INFO)