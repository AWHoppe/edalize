# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import re
import os
from collections import OrderedDict

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Jasper(Edatool):

    _description = """ Cadence Jasper Backend

Spyglass performs static source code analysis on HDL code and checks for common
coding errors or coding style violations.

Example snippet of a CAPI2 description file

::

   jasper:
     app: "superlint/xprop/cdc/"
     jasper_options:
       # prevent error SYNTH_5273 on generic RAM descriptions
       - handlememory yes

"""

    tool_options = {
        "members": {"app": "String"},
        "lists": {
            "jasper_options": "String",
        },
    }

    argtypes = ["vlogdefine", "vlogparam"]

    tool_options_defaults = {
        "app": "superlint",
        "jasper_options": [],
    }

    def _set_tool_options_defaults(self):
        for key, default_value in self.tool_options_defaults.items():
            if not key in self.tool_options:
                logger.info(
                    "Set Jasper tool option %s to default value %s"
                    % (key, str(default_value))
                )
                self.tool_options[key] = default_value

    def configure_main(self):
        """
        Configuration is the first phase of the build.

        This writes the project TCL files and Makefile. It first collects all
        sources, IPs and constraints and then writes them to the TCL file along
        with the build steps.
        """
        self._set_tool_options_defaults()

        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self._write_fileset_to_f_file(
            os.path.join(self.work_root, "%s.scr" % self.name ), include_vlogparams=False
        )

        tcl_source_files = [f for f in src_files if f.file_type == "tclSource"]
        waiver_files = [f for f in src_files if f.file_type == "waiver"]
        rules_files = [f for f in src_files if f.file_type == "jasperSuperlintRules"]

        template_vars = {
            "name": self.name,
            "src_files": src_files,
            "incdirs": incdirs,
            "jasper_options": self.tool_options["jasper_options"],
            "tcl_source_files": tcl_source_files,
            "waiver_files": waiver_files,
            "rules_files": rules_files,
            "toplevel": self.toplevel,
            "vlogparam": self.vlogparam,
            "vlogdefine": self.vlogdefine,
            "app": "",
        }

        # Create a single TCL file for the selected app
        app = self.tool_options["app"]
        sanitized_app = re.sub(r"[^a-zA-Z0-9]", "_", app).lower()
        template_vars["app"] = sanitized_app

        self.render_template(
            "run-jasper-app.tcl.j2",
            "run-jasper-%s.tcl" % sanitized_app,
            template_vars,
        )

        self.render_template("Makefile.j2", "Makefile", template_vars)

