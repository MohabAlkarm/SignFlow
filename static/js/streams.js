const APP_ID = "5812eca6e34c4aecae565ee3acdc1660";
const appCertificate = "08a0b81d3c984f45896e8cac9c4d0b0d";
const TOKEN = sessionStorage.getItem("token");
const CHANNEL = sessionStorage.getItem("room");
let UID = sessionStorage.getItem("UID");
const rtmToken = sessionStorage.getItem("rtmToken");
let NAME = sessionStorage.getItem("name");
let OTHER_USER_NAME = "";

const rtcClient = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });

let localTracks = [];
let remoteUsers = {};

let initiateRTM = async () => {
  let uid = "listener1";
  let token = rtmToken;

  const { RTM } = AgoraRTM;
  const rtm = new RTM(APP_ID, uid);

  try {
    const result = await rtm.login({ token: token });

    console.log(result);
  } catch (status) {
    console.log(status);
  }
  try {
    const result = await rtm.subscribe(CHANNEL);
    console.log(result);
  } catch (status) {
    console.log(status);
  }

  rtm.addEventListener("presence", (event) => {
    if (event.eventType == "JOIN") {
      console.log("NEW USER NAME: ", event.publisher);
    }
  });

  const publishMessage = async (message) => {
    const payload = { type: "text", message: message , sender: NAME};
    const publishMessage = JSON.stringify(payload);
    const publishOptions = { channelType: "MESSAGE" };
    try {
      const result = await rtm.publish(CHANNEL, publishMessage, publishOptions);
      console.log(result);
    } catch (status) {
      console.log(status);
    }
  };

  rtm.addEventListener("message", async (event) => {
    if (event.channelType === "USER") {
      document.getElementById(`subtitles-${NAME}`).innerText = event.message;
      await publishMessage(event.message);
      return;
    }

    let incomingMessage = JSON.parse(event.message);
    if (incomingMessage.sender !== NAME) {
      document.getElementById(`subtitles-${OTHER_USER_NAME}`).innerText = incomingMessage.message;
    }
  });
};

let joinAndDisplayLocalStream = async () => {
  document.getElementById("room-name").innerText = CHANNEL;

  rtcClient.on("user-published", handleUserJoined);
  rtcClient.on("user-left", handleUserLeft);

  try {
    UID = await rtcClient.join(APP_ID, CHANNEL, TOKEN, UID);
    initiateRTM();
  } catch (error) {
    console.error(error);
    window.open("/", "_self");
  }

  localTracks = await AgoraRTC.createMicrophoneAndCameraTracks();

  let member = await createMember();

  let player = `<div  class="video-container" id="user-container-${UID}">
                     <div class="video-player" id="user-${UID}"></div>
                     <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
                     <div class="subtitles" id="subtitles-${member.name}"></div>
                  </div>`;

  document
    .getElementById("video-streams")
    .insertAdjacentHTML("beforeend", player);
  localTracks[1].play(`user-${UID}`);
  await rtcClient.publish([localTracks[0], localTracks[1]]);

  let response = await fetch("/started_call/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
};

let handleUserJoined = async (user, mediaType) => {
  remoteUsers[user.uid] = user;
  await rtcClient.subscribe(user, mediaType);

  if (mediaType === "video") {
    let player = document.getElementById(`user-container-${user.uid}`);
    if (player != null) {
      player.remove();
    }

    let member = await getMember(user);

    player = `<div  class="video-container" id="user-container-${user.uid}">
            <div class="video-player" id="user-${user.uid}"></div>
            <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
            <div class="subtitles" id="subtitles-${member.name}"></div>
        </div>`;

    OTHER_USER_NAME = member.name;

    document
      .getElementById("video-streams")
      .insertAdjacentHTML("beforeend", player);
    user.videoTrack.play(`user-${user.uid}`);
  }

  if (mediaType === "audio") {
    user.audioTrack.play();
  }
};

let handleUserLeft = async (user) => {
  delete remoteUsers[user.uid];
  document.getElementById(`user-container-${user.uid}`).remove();
};

let leaveAndRemoveLocalStream = async () => {
  for (let i = 0; localTracks.length > i; i++) {
    localTracks[i].stop();
    localTracks[i].close();
  }

  await rtcClient.leave();

  try {
    const result = await rtm.unsubscribe(CHANNEL);
    console.log(result);
  } catch (status) {
    console.log(status);
  }
  //This is somewhat of an issue because if user leaves without actaull pressing leave button, it will not trigger
  deleteMember();
  let response = await fetch("/ended_call/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  window.open("/", "_self");
};

let toggleCamera = async (e) => {
  console.log("TOGGLE CAMERA TRIGGERED");
  if (localTracks[1].muted) {
    await localTracks[1].setMuted(false);
    e.target.style.backgroundColor = "#fff";
  } else {
    await localTracks[1].setMuted(true);
    e.target.style.backgroundColor = "rgb(255, 80, 80, 1)";
  }
};

let toggleMic = async (e) => {
  console.log("TOGGLE MIC TRIGGERED");
  if (localTracks[0].muted) {
    await localTracks[0].setMuted(false);
    e.target.style.backgroundColor = "#fff";
  } else {
    await localTracks[0].setMuted(true);
    e.target.style.backgroundColor = "rgb(255, 80, 80, 1)";
  }
};

let createMember = async () => {
  let response = await fetch("/create_member/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: NAME, room_name: CHANNEL, UID: UID }),
  });
  let member = await response.json();
  return member;
};

let getMember = async (user) => {
  let response = await fetch(
    `/get_member/?UID=${user.uid}&room_name=${CHANNEL}`
  );
  let member = await response.json();
  return member;
};

let deleteMember = async () => {
  let response = await fetch("/delete_member/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: NAME, room_name: CHANNEL, UID: UID }),
  });

  try {
    let response = await fetch(`/stop_translation`);
    console.log(response.status);
  } catch (error) {
    console.log(error);
  }
  let member = await response.json();
};

window.addEventListener("beforeunload", deleteMember);

joinAndDisplayLocalStream();

document
  .getElementById("leave-btn")
  .addEventListener("click", leaveAndRemoveLocalStream);
document.getElementById("camera-btn").addEventListener("click", toggleCamera);
document.getElementById("mic-btn").addEventListener("click", toggleMic);
