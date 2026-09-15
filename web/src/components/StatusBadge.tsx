const STATUS_CLASS: Record<string, string> = {
  DRAFT: "badge-draft",
  PUBLISHED: "badge-published",
  ARCHIVED: "badge-archived",
  PENDING: "badge-pending",
  UPLOADING: "badge-pending",
  UPLOADED: "badge-synced",
  SYNCED: "badge-synced",
  FAILED: "badge-failed",
};

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Draft",
  PUBLISHED: "Published",
  ARCHIVED: "Archived",
  PENDING: "Pending",
  UPLOADING: "Uploading",
  UPLOADED: "Uploaded",
  SYNCED: "Synced",
  FAILED: "Failed",
};

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge ${STATUS_CLASS[status] ?? "badge-draft"}`}>{STATUS_LABEL[status] ?? status}</span>;
}
