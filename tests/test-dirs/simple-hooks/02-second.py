#!/usr/bin/env python
import os

test_harness_dir = os.environ["TEST_HARNESS_DIR"]

with open(os.path.join(test_harness_dir, "hello"), "w") as f:
    f.write("hello")
