import CropRecordForm from "../components/CropRecordForm";
import CsvUploadForm from "../components/CsvUploadForm";
import { createHarvestEvent, createHarvestRecord, uploadHarvestRecordsCsv } from "../services/api";

export default function FieldEntryPage() {
  const submitRecord = async (payload) => {
    const harvestEvent = await createHarvestEvent(1, {
      harvest_date: new Date().toISOString().slice(0, 10)
    });
    await createHarvestRecord(harvestEvent.id, payload);
    alert("Record submission endpoint is wired.");
  };

  const uploadCsv = async (file) => {
    const harvestEvent = await createHarvestEvent(1, {
      harvest_date: new Date().toISOString().slice(0, 10)
    });
    return uploadHarvestRecordsCsv(harvestEvent.id, file);
  };

  return (
    <>
      <div className="panel">
        <h1>Lexington Field</h1>
        <p>New harvest record for today</p>
      </div>
      <CropRecordForm onSubmit={submitRecord} />
      <CsvUploadForm onUpload={uploadCsv} />
    </>
  );
}
