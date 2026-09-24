import io
import csv
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

class ExportService:
    def harvest_records_as_csv(self, db: Session) -> str:
        result = db.execute(
            text("SELECT * FROM testdb ORDER BY record_id")
        )
        rows = result.fetchall()
        columns = result.keys()

        output = io.StringIO(newline="")
        writer = csv.writer(output) # Writer will handle things like commas to make writing output more robust

        # Write column names
        writer.writerow(columns)

        # Write database rows
        for row in rows:
            formatted_row = []

            for value in row:
                #JSONB values may come back as py dictionaries/lists
                #Convert them to valid JSON before writing to our CSV
                if isinstance(value, (dict,list)):
                    value = json.dumps(value)

                formatted_row.append(value)
            writer.writerow(formatted_row)

        return output.getvalue()
