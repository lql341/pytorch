# Owner(s): ["oncall: quantization"]

import torch
# import torch.nn.quantized as nnq
from torch.testing._internal.common_quantization import (
    QuantizationTestCase,
    SingleLayerLinearModel,
)
from os.path import exists
from os import getcwd
import re


class TestQuantizationDocs(QuantizationTestCase):
    r"""
    The tests in this section import code from the quantization docs and check that
    they actually run. In cases where objects are undefined in the code snippet, they
    must be provided in the test. The imports seem to behave a bit inconsistently,
    they can be imported either in the test file or passed as a global input
    """

    def _get_code(self, path_from_pytorch, unique_identifier, offset=2, strict=True):
        r"""
        This function reads in the code from the docs, note that first and last
        line refer to the line number (first line of doc is 1), the offset due to
        python file reading is handled within this function. Most code snippets
        have a 2 space indentation, for other indentation levels, change offset,
        strict=True is to check that the line before the first line and the line after
        the last line are `newlines`, this is to ensure that the addition of a new line
        in the docs does not shift the code chunk out of the selection window.
        """
        def get_correct_path(path_from_pytorch):
            r"""
            Current working directory when CI is running test seems to vary, this function
            looks for the pytorch directory and if it finds it looks for the path to the
            file and if the file exists returns that path, otherwise keeps looking. Will
            only work if cwd contains pytorch or is somewhere in the pytorch repo.
            """

            # check if cwd contains pytorch
            if exists('./pytorch' + path_from_pytorch):
                return './pytorch' + path_from_pytorch

            # check if pytorch is cwd or a parent of cwd
            cur_dir_path = getcwd()
            folders = cur_dir_path.split('/')[::-1]
            path_prefix = './'
            for folder in folders:
                if folder == 'pytorch' and exists(path_prefix + path_from_pytorch):
                    return(path_prefix + path_from_pytorch)
                path_prefix = '.' + path_prefix
            # if not found
            return None

        path_to_file = get_correct_path(path_from_pytorch)
        if path_to_file:
            file = open(path_to_file)
            content = file.readlines()
            # if strict:
            #     assert content[first_line - 2] == "\n" and content[last_line] == "\n", (
            #         "The line before and after the code chunk should be a newline."
            #         "If new material was added to {}, please update this test with"
            #         "the new code chunk line numbers, previously the lines were "
            #         "{} to {}".format(path_to_file, first_line, last_line)
            #     )

            # it will register as having a newline at the end in python
            if "\n" not in unique_identifier:
                unique_identifier+="\n"

            assert unique_identifier in content, \
                "could not find {} in {}".format(unique_identifier, path_to_file)

            # get index of first line of code
            line_num_start = content.index(unique_identifier)+1

            # next find where the code chunk ends.
            # this regex will match lines that don't start
            # with a \n or "  " with number of spaces=offset
            r = r=re.compile("^[^\n,"+" "*offset+"]")
            # this will return the line of first line that matches regex
            line_after_code = next(filter(r.match, content[line_num_start:]))
            last_line_num = content.index(line_after_code)

            # remove the first `offset` chars of each line and gather it all together
            code = "".join([x[offset:] for x in content[line_num_start+1:last_line_num]])

            # want to make sure we are actually getting some code,
            assert last_line_num-line_num_start>300, \
                "The code in {} identified by {} seems suspiciously short:" \
                "\n\n###code-start####\n{}###code-end####".format(path_to_file, unique_identifier,code)
            return code
        return None


    def _test_code(self, code, global_inputs=None):
        r"""
        This function runs `code` using any vars in `global_inputs`
        """
        # if couldn't find the
        if code is not None:
            expr = compile(code, "test", "exec")
            exec(expr, global_inputs)

    def test_quantization_doc_ptdq(self):
        path_from_pytorch = "docs/source/quantization.rst"
        unique_identifier = "PTDQ API Example::"
        code = self._get_code(path_from_pytorch, unique_identifier)
        self._test_code(code)

    def test_quantization_doc_ptsq(self):
        path_from_pytorch = "docs/source/quantization.rst"
        unique_identifier = "PTSQ API Example::"
        code = self._get_code(path_from_pytorch, unique_identifier)
        self._test_code(code)

    def test_quantization_doc_qat(self):
        path_from_pytorch = "docs/source/quantization.rst"
        unique_identifier = "QAT API Example::"

        def _dummy_func(*args, **kwargs):
            return None

        input_fp32 = torch.randn(1, 1, 1, 1)
        global_inputs = {"training_loop": _dummy_func, "input_fp32": input_fp32}

        code = self._get_code(path_from_pytorch, unique_identifier)
        self._test_code(code, global_inputs)

    def test_quantization_doc_fx(self):
        path_from_pytorch = "docs/source/quantization.rst"
        unique_identifier = "FXPTQ API Example::"

        input_fp32 = SingleLayerLinearModel().get_example_inputs()
        global_inputs = {"UserModel": SingleLayerLinearModel, "input_fp32": input_fp32}

        code = self._get_code(path_from_pytorch, unique_identifier)
        self._test_code(code, global_inputs)

    def test_quantization_doc_custom(self):
        path_from_pytorch = "docs/source/quantization.rst"
        unique_identifier = "Custom API Example::"

        global_inputs = {"nnq": torch.nn.quantized}

        code = self._get_code(path_from_pytorch, unique_identifier)
        self._test_code(code, global_inputs)