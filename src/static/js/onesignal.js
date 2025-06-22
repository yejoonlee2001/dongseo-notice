// OneSignal 웹 푸시 알림 초기화 및 구독 관리
// onesignal.js

document.addEventListener('DOMContentLoaded', () => {
  // 알림 구독 버튼 요소
  const notificationBtn = document.getElementById('notification-subscribe-btn');
  const notificationStatus = document.getElementById('notification-status');
  
  // OneSignal 초기화
  window.OneSignal = window.OneSignal || [];
  
  // OneSignal 초기화 함수
  function initOneSignal() {
    OneSignal.push(function() {
      OneSignal.init({
        appId: "412bf56c-7f9d-48a5-9bb1-ced8f7f93755",
        safari_web_id: "YOUR_SAFARI_WEB_ID", // Safari 브라우저 지원을 위한 ID (선택사항)
        notifyButton: {
          enable: false, // 기본 구독 버튼 비활성화 (커스텀 버튼 사용)
        },
        allowLocalhostAsSecureOrigin: true, // 개발 환경에서 테스트 허용
      });
      
      // 초기 구독 상태 확인
      checkSubscriptionStatus();
      
      // 구독 상태 변경 이벤트 리스너
      OneSignal.on('subscriptionChange', function(isSubscribed) {
        console.log('구독 상태 변경:', isSubscribed);
        updateSubscriptionUI(isSubscribed);
      });
    });
  }
  
  // 구독 상태 확인 함수
  function checkSubscriptionStatus() {
    OneSignal.push(function() {
      OneSignal.isPushNotificationsEnabled(function(isEnabled) {
        console.log('푸시 알림 활성화 상태:', isEnabled);
        updateSubscriptionUI(isEnabled);
      });
    });
  }
  
  // 구독 UI 업데이트 함수
  function updateSubscriptionUI(isSubscribed) {
    if (!notificationBtn) return;
    
    if (isSubscribed) {
      notificationBtn.textContent = '알림 구독 중';
      notificationBtn.classList.remove('btn-primary');
      notificationBtn.classList.add('btn-success');
      if (notificationStatus) {
        notificationStatus.textContent = '새 공지사항이 등록되면 알림을 받습니다.';
        notificationStatus.classList.add('subscribed');
      }
    } else {
      notificationBtn.textContent = '알림 구독하기';
      notificationBtn.classList.remove('btn-success');
      notificationBtn.classList.add('btn-primary');
      if (notificationStatus) {
        notificationStatus.textContent = '알림 구독을 활성화하면 새 공지사항을 바로 확인할 수 있습니다.';
        notificationStatus.classList.remove('subscribed');
      }
    }
    
    notificationBtn.disabled = false;
  }
  
  // 구독 버튼 클릭 이벤트 처리
  if (notificationBtn) {
    notificationBtn.addEventListener('click', () => {
      notificationBtn.disabled = true;
      
      OneSignal.push(function() {
        OneSignal.isPushNotificationsEnabled(function(isEnabled) {
          if (isEnabled) {
            // 구독 해지
            OneSignal.setSubscription(false).then(() => {
              console.log('알림 구독이 해지되었습니다.');
              notificationBtn.disabled = false;
            }).catch(error => {
              console.error('구독 해지 중 오류 발생:', error);
              notificationBtn.disabled = false;
            });
          } else {
            // 구독 활성화
            OneSignal.registerForPushNotifications({
              modalPrompt: true
            }).then(() => {
              console.log('알림 구독이 활성화되었습니다.');
              notificationBtn.disabled = false;
              
              // 태그 추가 (선택사항)
              OneSignal.sendTag("user_type", "student").then(() => {
                console.log("태그가 추가되었습니다.");
              });
            }).catch(error => {
              console.error('구독 활성화 중 오류 발생:', error);
              notificationBtn.disabled = false;
            });
          }
        });
      });
    });
  }
  
  // OneSignal 초기화
  initOneSignal();
});
