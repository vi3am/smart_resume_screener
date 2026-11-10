export function filterScoredCandidates(results, query, minimumScore) {
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const scoreFloor = Number(minimumScore) || 0;

  return results.filter((result) => {
    if (Number(result.overall_score) < scoreFloor) return false;
    if (!normalizedQuery) return true;
    const searchableText = [
      result.candidate_name,
      result.filename,
      ...(result.matched_skills || []),
      ...(result.missing_skills || []),
    ].filter(Boolean).join(" ").toLocaleLowerCase();
    return searchableText.includes(normalizedQuery);
  });
}

function csvCell(value) {
  let text = String(value ?? "");
  if (/^[\t\r\n ]*[=+\-@]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

export function shortlistToCsv(results) {
  const headers = [
    "Rank",
    "Candidate",
    "Filename",
    "Overall score",
    "Skills score",
    "Experience score",
    "Education score",
    "Semantic score",
    "Matched skills",
    "Missing skills",
  ];
  const rows = results.map((result) => [
    result.rank,
    result.candidate_name,
    result.filename,
    result.overall_score,
    result.skills_score,
    result.experience_score,
    result.education_score,
    result.semantic_score,
    (result.matched_skills || []).join("; "),
    (result.missing_skills || []).join("; "),
  ]);
  return [headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n");
}
