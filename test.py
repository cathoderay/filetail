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
            def __init__(self, path, queue):
                self.queue = queue
                self.tail = filetail.Tail(path, max_sleep=5)
                threading.Thread.__init__(self)

            def run(self):
                while True:
                    line = self.tail.nextline()
                    self.queue.put(line)
                    if line.startswith('50'):
                        break
        
        queue = Queue.Queue()
        processor = LinesProcessor(self.filepath, queue)  
        processor.start()

        # write something in the file
        os.system('seq 0 41 > %s' % self.filepath)

        # rotate file
        rotate_file(self.filepath)
        
        # write things in new file
        os.system('seq 42 50 > %s' % self.filepath)
        
        # asserts that thread is running
        self.assertEqual(2, len(threading.enumerate()))

        # waits to filetail detects rotating and processes new content
        # rotating is detected after max_sleep seconds
        time.sleep(7)

        # asserts that thread have died
        self.assertEqual(1, len(threading.enumerate()))

        # getting read lines
        reads = []
        while queue.qsize() > 0:
            reads.append(int(queue.get().strip()))

        # asserts all lines were delivered from filetail 
        self.assertEqual(range(0, 51), reads)

    def test_reading_lines_without_backslash_n(self):
        class LinesProcessor(threading.Thread):
            def __init__(self, path, queue):
                self.queue = queue
                self.tail = filetail.Tail(path, max_sleep=1) 
                threading.Thread.__init__(self)

            def run(self):
                while True:
                    line = self.tail.nextline()
                    self.queue.put(line)
                    if line.startswith('11'):
                        break

        queue = Queue.Queue()
        processor = LinesProcessor(self.filepath, queue)
        processor.start()
        result = []

        # write something in the file
        os.system("seq 0 10 > %s" % self.filepath)

        # get the lines written
        for i in range(11):
            line = queue.get()
            result.append(int(line.strip()))

        # append a line without a \n
        os.system("echo -n '1' >> %s" % self.filepath)

        # give time to make sure line without \n was not delivered
        time.sleep(1)

        # assert that line was not delivered
        self.assertEqual(0, queue.qsize())

        # complete line
        os.system("echo '1' >> %s" % self.filepath)

        # give time to detect finished line
        time.sleep(1)

        # get last line
        result.append(int(queue.get().strip()))

        # asserting that all lines were read
        self.assertEqual(12, len(result))
        self.assertEqual(range(0, 12), result)


if __name__ == '__main__':
    unittest.main()
