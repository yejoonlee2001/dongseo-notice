document.addEventListener('DOMContentLoaded', () => {
    // 전역 변수
    let currentPage = 1;
    let totalPages = 1;
    let currentFilter = 'all';
    let currentSearch = '';
    
    // DOM 요소
    const noticeList = document.getElementById('notice-list');
    const pagination = document.getElementById('pagination');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const updateTimeSpan = document.getElementById('update-time');
    
    // 초기 데이터 로드
    loadNotices();
    
    // 이벤트 리스너 등록
    searchBtn.addEventListener('click', handleSearch);
    refreshBtn.addEventListener('click', handleRefresh);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.getAttribute('data-filter');
            setActiveFilter(filter);
            currentFilter = filter;
            currentPage = 1;
            loadNotices();
        });
    });
    
    // 공지사항 로드 함수
    function loadNotices() {
        // 로딩 상태 표시
        noticeList.innerHTML = '<tr><td colspan="5" class="text-center">공지사항을 불러오는 중...</td></tr>';
        
        // API 요청 URL 구성
        let url = `/api/notices?page=${currentPage}&filter=${currentFilter}`;
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }
        
        // API 요청
        fetch(url)
            .then(response => response.json())
            .then(data => {
                renderNotices(data.notices);
                renderPagination(data.page, Math.ceil(data.total / data.per_page));
                updateTimeSpan.textContent = data.last_updated;
            })
            .catch(error => {
                console.error('공지사항 로드 중 오류 발생:', error);
                noticeList.innerHTML = '<tr><td colspan="5" class="text-center">공지사항을 불러오는 중 오류가 발생했습니다.</td></tr>';
            });
    }
    
    // 공지사항 렌더링 함수
    function renderNotices(notices) {
        if (!notices || notices.length === 0) {
            noticeList.innerHTML = '<tr><td colspan="5" class="text-center">공지사항이 없습니다.</td></tr>';
            return;
        }
        
        let html = '';
        
        notices.forEach(notice => {
            const rowClass = notice.is_notice ? 'notice-row' : '';
            const newBadge = notice.is_new ? '<span class="new-badge">NEW</span>' : '';
            const attachmentIcon = notice.has_attachment ? '<i class="attachment-icon">📎</i>' : '';
            
            html += `
                <tr class="${rowClass}">
                    <td class="num">${notice.num}</td>
                    <td class="title">
                        <a href="${notice.link}" target="_blank">${notice.title}</a>
                        ${newBadge}
                        ${attachmentIcon}
                    </td>
                    <td class="author">${notice.author}</td>
                    <td class="date">${notice.date}</td>
                    <td class="views">${notice.views}</td>
                </tr>
            `;
        });
        
        noticeList.innerHTML = html;
    }
    
    // 페이지네이션 렌더링 함수
    function renderPagination(current, total) {
        currentPage = current;
        totalPages = total;
        
        if (total <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // 이전 페이지 버튼
        if (current > 1) {
            html += `<button onclick="changePage(${current - 1})">이전</button>`;
        }
        
        // 페이지 번호 버튼
        const startPage = Math.max(1, current - 2);
        const endPage = Math.min(total, current + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === current ? 'active' : '';
            html += `<button class="${activeClass}" onclick="changePage(${i})">${i}</button>`;
        }
        
        // 다음 페이지 버튼
        if (current < total) {
            html += `<button onclick="changePage(${current + 1})">다음</button>`;
        }
        
        pagination.innerHTML = html;
    }
    
    // 페이지 변경 함수
    window.changePage = function(page) {
        currentPage = page;
        loadNotices();
        window.scrollTo(0, 0);
    };
    
    // 검색 처리 함수
    function handleSearch() {
        currentSearch = searchInput.value.trim();
        currentPage = 1;
        loadNotices();
    }
    
    // 새로고침 처리 함수
    function handleRefresh() {
        refreshBtn.disabled = true;
        refreshBtn.textContent = '새로고침 중...';
        
        fetch('/api/notices/refresh')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadNotices();
                    updateTimeSpan.textContent = data.last_updated;
                }
            })
            .catch(error => {
                console.error('새로고침 중 오류 발생:', error);
            })
            .finally(() => {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '새로고침';
            });
    }
    
    // 필터 활성화 함수
    function setActiveFilter(filter) {
        filterBtns.forEach(btn => {
            if (btn.getAttribute('data-filter') === filter) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
});
