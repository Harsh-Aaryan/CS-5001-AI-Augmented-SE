const reviewOut = document.getElementById('reviewOut');
const draftOut = document.getElementById('draftOut');
const approveOut = document.getElementById('approveOut');
const improveOut = document.getElementById('improveOut');

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const payload = await res.json();
  if (!res.ok) {
    throw new Error(payload.error || payload.message || 'Request failed');
  }
  return payload;
}

document.getElementById('btnReview').addEventListener('click', async () => {
  reviewOut.textContent = '[Reviewer] Running diff analysis...';
  try {
    const payload = await postJson('/api/review', {
      base_branch: document.getElementById('reviewBase').value || null,
      commit_range: document.getElementById('reviewRange').value || null,
    });
    reviewOut.textContent = [
      '[Planner] Scope validated.',
      pretty(payload),
    ].join('\n\n');
    document.getElementById('draftReviewId').value = payload.review_id;
  } catch (err) {
    reviewOut.textContent = String(err);
  }
});

document.getElementById('btnDraft').addEventListener('click', async () => {
  draftOut.textContent = '[Writer] Drafting content...';
  try {
    const payload = await postJson('/api/draft', {
      kind: document.getElementById('draftKind').value,
      source: document.getElementById('draftSource').value,
      review_id: document.getElementById('draftReviewId').value || null,
      instruction: document.getElementById('draftInstruction').value || null,
    });
    draftOut.textContent = [
      '[Writer] Draft created.',
      `[Gatekeeper] Reflection verdict: ${payload.reflection.verdict}`,
      pretty(payload),
    ].join('\n\n');
    document.getElementById('approveDraftId').value = payload.draft_id;
  } catch (err) {
    draftOut.textContent = String(err);
  }
});

document.getElementById('btnApproveYes').addEventListener('click', async () => {
  approveOut.textContent = '[Gatekeeper] Approval YES received. Attempting create...';
  try {
    const payload = await postJson('/api/approve', {
      draft_id: document.getElementById('approveDraftId').value,
      approve: true,
    });
    approveOut.textContent = ['[Tool] GitHub API call successful.', pretty(payload)].join('\n\n');
  } catch (err) {
    approveOut.textContent = String(err);
  }
});

document.getElementById('btnApproveNo').addEventListener('click', async () => {
  approveOut.textContent = '[Gatekeeper] Approval NO received. Aborting...';
  try {
    const payload = await postJson('/api/approve', {
      draft_id: document.getElementById('approveDraftId').value,
      approve: false,
    });
    approveOut.textContent = [
      '[Gatekeeper] Draft rejected. No changes made.',
      pretty(payload),
    ].join('\n\n');
  } catch (err) {
    approveOut.textContent = String(err);
  }
});

document.getElementById('btnImprove').addEventListener('click', async () => {
  improveOut.textContent = '[Reviewer] Inspecting existing item...';
  try {
    const payload = await postJson('/api/improve', {
      kind: document.getElementById('improveKind').value,
      number: Number(document.getElementById('improveNumber').value),
    });
    improveOut.textContent = [
      '[Reviewer] Critique generated.',
      '[Writer] Proposed improved structured version.',
      `[Gatekeeper] Reflection verdict: ${payload.reflection.verdict}`,
      pretty(payload),
    ].join('\n\n');
  } catch (err) {
    improveOut.textContent = String(err);
  }
});
