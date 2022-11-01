from incipyt import project, signals, tools

classifiers = {
    "Copyright": "License :: Other/Proprietary License",
    "Apache 2.0": "License :: OSI Approved :: Apache Software License",
    "BSD 2-Clause": "License :: OSI Approved :: BSD License",
    "BSD 3-Clause": "License :: OSI Approved :: BSD License",
    "CDDL 1.0": "License :: OSI Approved :: Common Development and Distribution License 1.0 (CDDL-1.0)",
    "EPL 2.0": "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
    "GPL 2.0": "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    "GPL 3.0": "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "LGPL 2.0": "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
    "LGPL 2.1": "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
    "LGPL 3.0": "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "MIT": "License :: OSI Approved :: MIT License",
    "MPL 2.0": "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
}


class License(tools.Tool):
    """Include a license to :class:`incipyt.project._Structure`."""

    def add_to_structure(self):
        """Add license file to `project.structure` based on `LICENSE` environ."""
        template_name = "licenses/%s.txt" % project.environ["LICENSE"].replace(" ", "-")
        project.structure.use_template(template_name, dest="LICENSE")

    def pre(self, workon):
        """Emit LICENSE to the classifiers.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        signals.classifier.emit(classifier=classifiers[project.environ["LICENSE"]])
