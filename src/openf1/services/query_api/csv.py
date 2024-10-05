import csv
import io


def generate_csv_response(rows: list[dict], filename: str):
    """Takes a list of results and a filename, creates a CSV file in memory, and returns
    it as a PlainTextResponse with appropriate headers for file download.
    """
    if len(rows) == 0:
        raise ValueError("No results")

    # Import it here to prevent a weird circular import
    from fastapi.responses import PlainTextResponse

    output = io.StringIO()
    field_names = set().union(*rows)
    csv_writer = csv.DictWriter(output, fieldnames=sorted(field_names))
    csv_writer.writeheader()

    for row in rows:
        csv_writer.writerow(row)
    csv_data = output.getvalue()

    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return PlainTextResponse(content=csv_data, media_type="text/csv", headers=headers)
