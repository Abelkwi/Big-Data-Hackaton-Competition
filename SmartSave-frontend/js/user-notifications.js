(function () {
  if (typeof API === 'undefined' || !API.isAuthenticated()) return;

  const style = document.createElement('style');
  style.textContent = `
    .ss-notice { position:fixed; top:78px; right:20px; z-index:1000; font:13px/1.5 Inter,system-ui,sans-serif; }
    .ss-notice-toggle { position:relative; width:42px; height:42px; border:1px solid #dfe7ed; border-radius:50%; background:#fff; color:#20354b; box-shadow:0 4px 16px #17253c1c; font-size:19px; cursor:pointer; }
    .ss-notice-count { position:absolute; top:-3px; right:-4px; min-width:17px; height:17px; padding:0 4px; border:2px solid #fff; border-radius:12px; background:#c95757; color:#fff; font:700 9px/13px Inter,system-ui,sans-serif; }
    .ss-notice-panel { position:absolute; top:49px; right:0; width:min(360px,calc(100vw - 24px)); max-height:70vh; overflow:auto; border:1px solid #e4eaf0; border-radius:13px; background:#fff; box-shadow:0 14px 40px #17253c26; }
    .ss-notice-head { display:flex; align-items:center; justify-content:space-between; gap:9px; padding:13px; border-bottom:1px solid #e8edf2; color:#243247; font-weight:700; }
    .ss-notice-head button,.ss-notice-row button,.ss-notice-more { border:0; background:none; color:#4778c7; font:600 11px Inter,system-ui,sans-serif; cursor:pointer; }
    .ss-notice-row { padding:11px 13px; border-bottom:1px solid #eef1f4; color:#243247; }
    .ss-notice-row.unread { background:#f3f7ff; }
    .ss-notice-row strong { display:block; font-size:11px; }
    .ss-notice-row p { margin:4px 0; color:#58677a; font-size:10px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .ss-notice-row time { display:block; color:#8793a2; font-size:9px; }
    .ss-notice-row button { margin-top:5px; }
    .ss-notice-empty { padding:18px 13px; color:#8793a2; font-size:11px; text-align:center; }
    .ss-notice-more { width:100%; padding:11px; }
    @media(max-width:520px) { .ss-notice { top:68px; right:12px; } }
  `;
  document.head.append(style);

  const root = document.createElement('div');
  root.className = 'ss-notice';
  const toggle = document.createElement('button');
  toggle.className = 'ss-notice-toggle';
  toggle.type = 'button';
  toggle.setAttribute('aria-label', 'Open notifications');
  toggle.setAttribute('aria-expanded', 'false');
  toggle.textContent = '🔔';
  const count = document.createElement('span');
  count.className = 'ss-notice-count';
  count.hidden = true;
  toggle.append(count);
  const panel = document.createElement('section');
  panel.className = 'ss-notice-panel';
  panel.hidden = true;
  panel.setAttribute('aria-label', 'Notifications');
  root.append(toggle, panel);
  document.body.append(root);

  let page = 1;
  let hasMore = false;
  let isLoading = false;

  function button(text, onClick) {
    const element = document.createElement('button');
    element.type = 'button';
    element.textContent = text;
    element.addEventListener('click', onClick);
    return element;
  }

  async function loadNotifications(append = false) {
    if (isLoading) return;
    isLoading = true;
    try {
      const [response, unread] = await Promise.all([
        API.getNotifications({ page: append ? page + 1 : 1 }),
        API.getUnreadNotificationCount(),
      ]);
      const notifications = Array.isArray(response) ? response : response.results || [];
      if (!append) {
        page = 1;
        panel.replaceChildren();
        const header = document.createElement('div');
        header.className = 'ss-notice-head';
        const heading = document.createElement('span');
        heading.textContent = 'Notifications';
        header.append(heading);
        const unreadNotifications = Number(unread.unread_count) || 0;
        if (unreadNotifications) {
          header.append(button('Mark all read', async () => {
            try {
              await API.markAllNotificationsRead();
              await loadNotifications();
            } catch (error) {
              console.error('Unable to mark notifications as read:', error);
            }
          }));
        }
        panel.append(header);
      } else {
        page += 1;
        panel.querySelector('.ss-notice-more')?.remove();
      }

      count.textContent = Number(unread.unread_count) > 99 ? '99+' : String(unread.unread_count || '');
      count.hidden = !Number(unread.unread_count);
      notifications.forEach((notification) => {
        const row = document.createElement('article');
        row.className = `ss-notice-row${notification.is_read ? '' : ' unread'}`;
        const title = document.createElement('strong');
        title.textContent = notification.title;
        const body = document.createElement('p');
        body.textContent = notification.body || notification.type_label || '';
        const date = document.createElement('time');
        date.dateTime = notification.created_at || '';
        date.textContent = notification.created_at
          ? new Date(notification.created_at).toLocaleString()
          : '';
        row.append(title, body, date);
        if (!notification.is_read) {
          row.append(button('Mark read', async () => {
            try {
              await API.markNotificationRead(notification.id);
              await loadNotifications();
            } catch (error) {
              console.error('Unable to mark notification as read:', error);
            }
          }));
        }
        panel.append(row);
      });

      hasMore = Boolean(Array.isArray(response) ? false : response.next);
      if (!panel.querySelector('.ss-notice-row')) {
        const empty = document.createElement('div');
        empty.className = 'ss-notice-empty';
        empty.textContent = 'You have no notifications yet.';
        panel.append(empty);
      }
      if (hasMore) panel.append(button('Show older notifications', () => loadNotifications(true)));
    } catch (error) {
      const message = document.createElement('div');
      message.className = 'ss-notice-empty';
      message.textContent = 'Notifications could not be loaded. Please try again.';
      panel.replaceChildren(message);
      console.error('Unable to load notifications:', error);
    } finally {
      isLoading = false;
    }
  }

  toggle.addEventListener('click', async () => {
    const open = panel.hidden;
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    if (open) await loadNotifications();
  });
  document.addEventListener('click', (event) => {
    if (!root.contains(event.target)) {
      panel.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
  loadNotifications();
})();
