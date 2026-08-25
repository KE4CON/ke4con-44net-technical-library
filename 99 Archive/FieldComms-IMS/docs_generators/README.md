# FieldComms Documentation Generators

## CRITICAL — READ THIS FIRST

These scripts build all FieldComms documentation PDFs.
**They are DELETED when a Claude session ends.**
**They MUST be committed to GitHub after every editing session.**

## Rule for Claude

At the end of every session that modifies a generator, Claude must:
1. Copy the updated script to fieldcomms/docs_generators/
2. Copy the updated PDF to fieldcomms/docs/
3. Run: git add docs_generators/ docs/ && git commit -m "Save generators + PDFs" && git push

## Documents and generators

| PDF | Generator | Status |
|-----|-----------|--------|
| FieldComms_Installation_Guide.pdf | gen_install_guide.py | LOST - needs rebuild |
| FieldComms_Complete_User_Manual_v1.0.pdf | manual_build.py + manual_ch_*.py | LOST - needs rebuild |
| McHenry_County_RACES_*.pdf | gen_user_guide.py | LOST - needs rebuild |
| FieldComms_Field_Quick_Reference.pdf | gen_field_quickref.py | LOST - needs rebuild |
| ESV_Beta_Test_Checklist.pdf | beta_checklist_build.py | LOST - needs rebuild |
| IncidentManagement_Overview.pdf | overview_build.py | PRESENT |

## To rebuild a lost generator

Tell Claude: "Rebuild the [document name] generator from the current PDF"
Claude will read the PDF and reconstruct the generator script.
