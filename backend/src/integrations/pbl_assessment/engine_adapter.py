from pathlib import Path


class AssessmentEngineAdapter:
    def __init__(self, pbl_assessment_root: Path):
        self.pbl_assessment_root = pbl_assessment_root

    def run_assessment(self, manifest_path: str, output_dir: str, db_path: str):
        raise NotImplementedError("Assessment engine not configured")
