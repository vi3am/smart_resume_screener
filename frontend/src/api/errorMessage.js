export function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === "string" ? item : item?.msg))
      .filter((message) => typeof message === "string" && message.trim());
    if (messages.length) return messages.join("; ");
  }

  return error?.message || fallback;
}
