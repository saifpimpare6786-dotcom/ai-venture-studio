# Workflow: Add Report Type
Trigger: `/add-report-type <name>`

Use this whenever adding one of the remaining report types (tier 2 in `skills/report-generation/SKILL.md`) or any new report type.

## Steps
1. Define a pydantic schema for the new report type's required sections
2. Write a prompt template that maps pipeline state (`specialized_outputs`, `council_feedback`, `scores`) into that schema
3. Register the new type in the Report Generator's report-type registry (config entry, not new if/else branches)
4. Declare supported export formats (DOCX / PPTX / PDF) for this type and add the export mapping
5. Add a frontend view/tab for the new report type under the Reports module
6. Generate a test report end-to-end using a fixed mock business idea input, verify all required sections populate
7. Use the Browser Subagent to confirm the new report renders correctly in the frontend Reports view
8. Commit
