const BASE_URL = "http://127.0.0.1:8000";

function safeJsonParse(value, fallback = null){
  try{
    return JSON.parse(value);
  }catch{
    return fallback;
  }
}

function setStatus(id, message, type = "loading"){
  const el = document.getElementById(id);
  if(!el) return;
  el.className = `status show ${type}`;
  el.textContent = message;
}

function clearStatus(id){
  const el = document.getElementById(id);
  if(!el) return;
  el.className = "status";
  el.textContent = "";
}

function go(url){
  window.location.href = url;
}

function escapeHtml(str){
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getUser(){
  return safeJsonParse(localStorage.getItem("user"), null);
}

function requireUser(){
  const user = getUser();
  if(!user){
    go("login.html");
    return null;
  }
  return user;
}

function logout(){
  localStorage.removeItem("user");
  localStorage.removeItem("analysis");
  localStorage.removeItem("chatSessionId");
  go("login.html");
}

async function uploadDocument(file, language){
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", language);

  const res = await fetch(`${BASE_URL}/upload-document`, {
    method: "POST",
    body: formData
  });

  const data = await res.json();
  if(!res.ok){
    throw new Error(data.detail || "Upload failed");
  }
  return data;
}

async function analyzeDocument(documentId, language){
  const res = await fetch(`${BASE_URL}/analyze-document`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      document_id: documentId,
      language
    })
  });

  const data = await res.json();
  if(!res.ok){
    throw new Error(data.detail || "Analysis failed");
  }
  return data;
}

async function startChat(documentId, language){
  const res = await fetch(`${BASE_URL}/start-chat`, {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      document_id: documentId,
      language
    })
  });

  const data = await res.json();
  if(!res.ok){
    throw new Error(data.detail || "Failed to start chat");
  }
  return data;
}

async function sendChatMessage(sessionId, question, language){
  const res = await fetch(`${BASE_URL}/chat`, {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      session_id: sessionId,
      question,
      language
    })
  });

  const data = await res.json();
  if(!res.ok){
    throw new Error(data.detail || "Chat failed");
  }
  return data;
}

async function runDecisionRisk(documentId, language, userDecision){
  const res = await fetch(`${BASE_URL}/decision-risk`, {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      document_id: documentId,
      language,
      user_decision: userDecision
    })
  });

  const data = await res.json();
  if(!res.ok){
    throw new Error(data.detail || "Risk analysis failed");
  }
  return data;
}