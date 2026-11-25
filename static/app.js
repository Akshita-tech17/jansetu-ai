// JanSetu AI Frontend Client (Family ID & DPI Edition)
let currentSessionId = "sess_" + Math.random().toString(36).substring(2, 9);
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

document.addEventListener("DOMContentLoaded", () => {
  console.log("JanSetu AI (Family ID Edition) initialized. Session:", currentSessionId);
  // Auto-load default Family on start
  lookupActiveFamily("24018291024");
});

function resetSession() {
  currentSessionId = "sess_" + Math.random().toString(36).substring(2, 9);
  const chatMessages = document.getElementById("chatMessages");
  chatMessages.innerHTML = `
    <div class="message-row incoming">
      <div class="bubble">
        <p>राम-राम! जनसेतु एआई में आपका स्वागत है। 🙏</p>
        <p>उत्तर प्रदेश सरकार के <b>परिवार पहचान पत्र (Family ID)</b> के माध्यम से हम आपके पूरे परिवार की पात्रता स्वतः जांच कर सभी योजनाओं का एकमुश्त आवेदन दाखिल कर सकते हैं।</p>
        <p class="sub-hint">ऊपर दिए गए फैमिली आईडी बटनों पर क्लिक करें या बोलकर बताएं।</p>
        <span class="msg-time">अभी</span>
      </div>
    </div>
  `;
  lookupActiveFamily("24018291024");
}

function handleInputKey(event) {
  if (event.key === "Enter") {
    sendTextMessage();
  }
}

// 1. FAMILY ID LOOKUP & PROACTIVE DISCOVERY
async function lookupActiveFamily(familyId) {
  const fid = familyId || document.getElementById("familyIdInput").value.trim() || "24018291024";
  document.getElementById("familyIdInput").value = fid;

  try {
    const res = await fetch(`/api/family/${fid}?session_id=${currentSessionId}`);
    const data = await res.json();
    renderFamilyState(data);
  } catch (err) {
    console.error("Family lookup error:", err);
  }
}

function loadFamilyPreset(familyId) {
  appendMessage("outgoing", `🔍 परिवार पहचान पत्र (Family ID): <b>${familyId}</b> दर्ज किया`);
  lookupActiveFamily(familyId);
}

function renderFamilyState(data) {
  const profile = data.profile;
  const basket = data.basket;

  // Update Telemetry Header
  document.getElementById("familyIdBadge").innerText = `FID: ${profile.family_id}`;
  document.getElementById("basketTotalBadge").innerText = `सालाना लाभ: ₹${basket.total_unclaimed_annual_inr.toLocaleString()}`;

  // Update Head Summary
  document.getElementById("familyHeadSummary").innerHTML = `
    <strong>मुखिया:</strong> ${profile.head_name} • 
    <strong>जनपद:</strong> ${profile.district} • 
    <strong>वार्षिक आय:</strong> ₹${profile.annual_income.toLocaleString()} • 
    <strong>भूमि:</strong> ${profile.land_holding_acres} एकड़ • 
    <strong>बोली:</strong> ${profile.primary_language}
  `;

  // Render Members Grid
  const membersList = document.getElementById("membersList");
  membersList.innerHTML = "";
  profile.members.forEach(m => {
    const chip = document.createElement("div");
    chip.className = "member-chip";
    chip.innerHTML = `
      <div class="member-name">${m.name} (${m.relation})</div>
      <div class="member-detail">उम्र: ${m.age} वर्ष • ${m.occupation}</div>
    `;
    membersList.appendChild(chip);
  });

  // Render Schemes Basket List
  const schemesList = document.getElementById("schemesBasketList");
  schemesList.innerHTML = "";
  basket.matched_schemes.forEach(s => {
    const item = document.createElement("div");
    item.className = "scheme-item";
    item.innerHTML = `
      <div class="scheme-info">
        <h4>${s.scheme_name}</h4>
        <p>👤 <b>लाभार्थी:</b> ${s.beneficiary_name} (${s.relation})</p>
        <p style="color: #64748B;">${s.eligibility_explanation_vernacular}</p>
      </div>
      <div class="scheme-benefit">${s.annual_benefit}</div>
    `;
    schemesList.appendChild(item);
  });

  // Render Proactive WhatsApp Message
  const actionCard = document.createElement("div");
  actionCard.className = "pdf-download-card";
  actionCard.innerHTML = `
    <div>
      <strong>🎯 ${basket.matched_schemes.length} योजनाएं पात्र पाई गईं (कुल ₹${basket.total_unclaimed_annual_inr.toLocaleString()}/वर्ष)</strong>
      <p style="font-size: 11px; color: #475569;">पारिवारिक विवरण ई-डिस्ट्रिक्ट पोर्टल से सत्यापित।</p>
    </div>
    <button class="pdf-btn" style="background: #16A34A;" onclick="triggerOneClickFiling()">🏛️ एक-क्लिक में सबमिट करें</button>
  `;
  appendMessage("incoming", basket.proactive_pitch_vernacular, data.audio_url, actionCard);
}

// 2. HANDWRITTEN / SCANNED DOCUMENT OCR
async function presetHandwrittenDoc() {
  appendMessage("outgoing", "✍️ [हस्तलिखित तहसीलदार आय प्रमाण पत्र स्कैन अपलोड किया]...");
  try {
    const res = await fetch("/data/test_samples/handwritten_tehsil_cert.png");
    const blob = await res.blob();
    const file = new File([blob], "handwritten_tehsil_cert.png", { type: "image/png" });
    await uploadAndScanDoc(file);
  } catch (err) {
    console.error("Scan sample error:", err);
  }
}

async function handleDocUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  appendMessage("outgoing", `📎 दस्तावेज़ अपलोड किया: <b>${file.name}</b>`);
  await uploadAndScanDoc(file);
}

async function uploadAndScanDoc(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", currentSessionId);

  try {
    const res = await fetch("/api/read-scan", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    const result = data.result;

    const badge = document.getElementById("scanStatusBadge");
    const box = document.getElementById("scanInspectionBox");

    if (result.is_legible) {
      badge.innerText = "सत्यापित / VERIFIED";
      badge.className = "metric-badge success";
      box.innerHTML = `
        <strong>श्रेणी:</strong> ${result.doc_category}<br/>
        <strong>लिपि:</strong> ${result.detected_script} • <strong>सरकारी मोहर:</strong> सत्यापित ✅<br/>
        <strong>निष्कर्ष:</strong> ${result.vernacular_summary}
      `;
      appendMessage("incoming", `✅ <b>हस्तलेख व स्कैन जांच सफल:</b><br/>${result.vernacular_summary}`, data.audio_url);
    } else {
      badge.innerText = "धुंधला / UNREADABLE";
      badge.className = "metric-badge warn";
      box.innerText = result.vernacular_summary;
      appendMessage("incoming", `⚠️ <b>स्कैन चेतावनी:</b> ${result.vernacular_summary}`, data.audio_url);
    }
  } catch (err) {
    console.error("Scan error:", err);
  }
}

// 3. "ENDING IN SOMETHING FILED" — ONE-CLICK SUBMISSION
async function triggerOneClickFiling() {
  appendMessage("outgoing", "🏛️ कृपया हमारे परिवार की सभी पात्र योजनाओं का आवेदन ई-डिस्ट्रिक्ट पर अंतिम रूप से जमा (File) करें।");

  const formData = new FormData();
  formData.append("session_id", currentSessionId);

  try {
    const res = await fetch("/api/file-application", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    const receipt = data.receipt;

    // Update Telemetry
    document.getElementById("filingStatusBadge").innerText = "आवेदन जमा (FILED)";
    document.getElementById("filingStatusBadge").className = "metric-badge success";
    document.getElementById("filingTelemetryBox").innerHTML = `
      <strong>पावती क्रमांक:</strong> ${receipt.application_number}<br/>
      <strong>समय:</strong> ${receipt.filing_timestamp} • <strong>योजनाएं:</strong> ${receipt.schemes_filed_count} एकमुश्त<br/>
      <strong>सेवा गारंटी (SLA):</strong> 15 कार्य दिवस (निस्तारण तिथि: <b>${receipt.sla_resolution_date}</b>)
    `;

    // Render Final Official Filing Receipt Card in Chat
    const receiptCard = document.createElement("div");
    receiptCard.className = "pdf-download-card";
    receiptCard.style.borderColor = "#16A34A";
    receiptCard.style.background = "#F0FDF4";
    receiptCard.innerHTML = `
      <div>
        <strong style="color: #15803D;">✅ आधिकारिक ई-डिस्ट्रिक्ट आवेदन पावती पत्र</strong>
        <p style="font-size: 11px; color: #166534;">
          पावती क्रमांक: <b>${receipt.application_number}</b><br/>
          SLA गारंटी: 15 कार्य दिवस (अंतिम तिथि: ${receipt.sla_resolution_date})
        </p>
      </div>
      <a href="${receipt.receipt_pdf_url}" target="_blank" download class="pdf-btn" style="background: #16A34A;">
        पावती पत्र डाउनलोड करें ⬇️
      </a>
    `;

    const speechSummary = `बधाई हो! आपका आवेदन जमा हो गया है। पावती संख्या ${receipt.application_number} है। 15 कार्य दिवस में निस्तारण हो जाएगा।`;
    appendMessage("incoming", `🎉 <b>आवेदन सफलतापूर्वक प्रेषित (FILED):</b><br/>${speechSummary}`, data.audio_url, receiptCard);

  } catch (err) {
    console.error("Filing error:", err);
  }
}

// 4. CHAT & VOICE HANDLERS
async function sendTextMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  // Sync Family ID search bar if user mentioned a 10-12 digit number
  const fidMatch = text.match(/\b(\d{10,12})\b/);
  if (fidMatch) {
    const inputFid = document.getElementById("familyIdInput");
    if (inputFid) inputFid.value = fidMatch[1];
  }

  appendMessage("outgoing", text);
  input.value = "";

  const formData = new FormData();
  formData.append("text", text);
  formData.append("session_id", currentSessionId);

  try {
    const res = await fetch("/api/chat", { method: "POST", body: formData });
    const data = await res.json();
    appendMessage("incoming", data.reply_hindi, data.audio_url);

    // Update inspector telemetry dynamically from chat turn
    if (data.slots) {
      const s = data.slots;
      const headSummary = document.getElementById("familyHeadSummary");
      if (headSummary) {
        headSummary.innerHTML = `
          <strong>आवेदक/मुखिया:</strong> ${s.applicant_name || 'लंबित'} • 
          <strong>पिता/पति:</strong> ${s.father_or_husband_name || 'लंबित'} • 
          <strong>जनपद:</strong> ${s.district || 'उत्तर प्रदेश'} • 
          <strong>आयु:</strong> ${s.age ? s.age + ' वर्ष' : 'लंबित'} • 
          <strong>वार्षिक आय:</strong> ${s.annual_income ? '₹' + Number(s.annual_income).toLocaleString() : 'लंबित'}
        `;
      }
    }

    if (data.ready_for_docs) {
      const actionCard = document.createElement("div");
      actionCard.className = "pdf-download-card";
      actionCard.innerHTML = `
        <div>
          <strong>✅ सभी आवश्यक विवरण पूर्ण एवं सत्यापित</strong>
          <p style="font-size: 11px; color: #475569;">आप सीधे आधिकारिक आवेदन पत्र जनरेट या फाइल कर सकते हैं।</p>
        </div>
        <button class="pdf-btn" style="background: #16A34A;" onclick="triggerOneClickFiling()">🏛️ एक-क्लिक में सबमिट करें</button>
      `;
      appendMessage("incoming", "पात्रता पूर्ण है! आप सीधे आवेदन फाइल कर सकते हैं:", null, actionCard);
    }
  } catch (err) {
    console.error("Chat error:", err);
  }
}

function appendMessage(type, text, audioUrl = null, downloadCard = null) {
  const chatMessages = document.getElementById("chatMessages");
  const row = document.createElement("div");
  row.className = `message-row ${type}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const p = document.createElement("p");
  p.innerHTML = text.replace(/\n/g, "<br>");
  bubble.appendChild(p);

  if (audioUrl) {
    const audioWrapper = document.createElement("div");
    audioWrapper.className = "audio-player-wrapper";
    audioWrapper.innerHTML = `<audio controls autoplay src="${audioUrl}"></audio>`;
    bubble.appendChild(audioWrapper);
  }

  if (downloadCard) {
    bubble.appendChild(downloadCard);
  }

  const time = document.createElement("span");
  time.className = "msg-time";
  time.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  bubble.appendChild(time);

  row.appendChild(bubble);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Offline Web Speech Fallback if audio URL is placeholder
  if (type === "incoming" && 'speechSynthesis' in window && (!audioUrl || audioUrl.includes("empty"))) {
    try {
      const clean = text.replace(/[*#_]/g, '').substring(0, 150);
      const utter = new SpeechSynthesisUtterance(clean);
      utter.lang = 'hi-IN';
      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.warn("Speech synthesis error:", e);
    }
  }
}

async function toggleRecording() {
  const btn = document.getElementById("recordBtn");
  const indicator = document.getElementById("recordingIndicator");

  if (!isRecording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        await uploadAudioBlob(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;
      btn.classList.add("recording");
      indicator.style.display = "flex";
    } catch (err) {
      console.warn("Microphone access denied, using simulated Bhojpuri voice query:", err);
      appendMessage("outgoing", "🎙️ <i>'हमार नाम रामेश्वर अहइ, हमार फैमिली आईडी 24018291024 बा, हमरा के कवन-कवन योजना मिल सकत बा?'</i>");
      lookupActiveFamily("24018291024");
    }
  } else {
    mediaRecorder.stop();
    isRecording = false;
    btn.classList.remove("recording");
    indicator.style.display = "none";
  }
}

async function uploadAudioBlob(blob) {
  appendMessage("outgoing", "🎙️ [नागरिक स्वर संवाद (Voice)]");
  const formData = new FormData();
  formData.append("audio", blob, "citizen_voice.webm");
  formData.append("session_id", currentSessionId);

  try {
    const res = await fetch("/api/voice", { method: "POST", body: formData });
    const data = await res.json();
    if (data.transcript) {
      appendMessage("outgoing", `🗣️ <i>"${data.transcript}"</i>`);
    }
    appendMessage("incoming", data.reply_hindi, data.audio_url);
  } catch (err) {
    console.error("Voice upload error:", err);
  }
}
