import os
import time
import Queue
import shutil
import unittest
import filetail
import threading


def rotate_file(filepath):
    os.rename(filepath, filepath + '.backup')
    open(filepath, 'w').close()


def create_file(filepath):
    return open(filepath, 'w')


class TestFileTail(unittest.TestCase):
    def setUp(self):
        self.working_dir = os.path.join('/tmp', 'filetail')
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
        os.chdir(self.working_dir)
        self.filename = 'test.log'
        self.filepath = (os.path.join(self.working_dir,
                                      self.filename))
        create_file(self.filepath)

    def tearDown(self):
        shutil.rmtree(self.working_dir)


    def test_rotating_file(self):
        class LinesProcessor(threading.Thread):
            def __init__(self, path):
                self.tail = filetail.Tail(path, max_sleep=5)
                threading.Thread.__init__(self)

            def run(self):
                while True:
                    line = self.tail.nextline()
                    if line.startswith('42'):
                        break
        
        processor = LinesProcessor(self.filepath)  
        processor.start()

        #write something in the file
        os.system('seq 0 41 > %s' % self.filepath)

        #rotate file
        rotate_file(self.filepath)
        
        #write things in new file
        os.system('seq 42 50 > %s' % self.filepath)
        
        #asserts that thread is running
        self.assertEqual(2, len(threading.enumerate()))

        #waits to filetail detects rotating
        time.sleep(6)
            
        #asserts that thread have died
        self.assertEqual(1, len(threading.enumerate()))


if __name__ == '__main__':
    unittest.main()
