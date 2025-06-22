import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dongseo_crawler')

class DongseoNoticeCrawler:
    """동서대학교 공지사항 크롤러 클래스"""
    
    def __init__(self):
        self.base_url = "https://www.dongseo.ac.kr/kr/index.php"
        self.notice_url = f"{self.base_url}?pCode=MN2000194"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def crawl_notices(self, max_pages=5):
        """
        공지사항 목록을 크롤링합니다.
        
        Args:
            max_pages (int): 크롤링할 최대 페이지 수
            
        Returns:
            list: 공지사항 목록 (딕셔너리 리스트)
        """
        all_notices = []
        
        try:
            for page in range(1, max_pages + 1):
                logger.info(f"페이지 {page} 크롤링 중...")
                
                # 페이지 URL 구성
                page_url = f"{self.notice_url}&page={page}"
                
                # 페이지 요청
                response = requests.get(page_url, headers=self.headers)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
                
                # HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 공지사항 테이블 찾기
                notice_table = soup.select_one('.board_list')
                if not notice_table:
                    logger.warning(f"페이지 {page}에서 공지사항 테이블을 찾을 수 없습니다.")
                    continue
                
                # 공지사항 행 추출
                notice_rows = notice_table.select('tbody tr')
                if not notice_rows:
                    logger.warning(f"페이지 {page}에서 공지사항 행을 찾을 수 없습니다.")
                    continue
                
                # 각 행에서 정보 추출
                for row in notice_rows:
                    try:
                        # 번호
                        num_cell = row.select_one('.num')
                        num = num_cell.get_text(strip=True) if num_cell else ""
                        
                        # 제목 및 링크
                        title_cell = row.select_one('.title')
                        title = title_cell.get_text(strip=True) if title_cell else ""
                        
                        # 링크 추출
                        link_tag = title_cell.select_one('a') if title_cell else None
                        link = self.base_url + link_tag['href'] if link_tag and 'href' in link_tag.attrs else ""
                        
                        # 작성자
                        author_cell = row.select_one('.author')
                        author = author_cell.get_text(strip=True) if author_cell else ""
                        
                        # 등록일
                        date_cell = row.select_one('.date')
                        date = date_cell.get_text(strip=True) if date_cell else ""
                        
                        # 조회수
                        views_cell = row.select_one('.views')
                        views = views_cell.get_text(strip=True) if views_cell else ""
                        
                        # 공지 여부 (class에 'notice' 포함 여부)
                        is_notice = 'notice' in row.get('class', [])
                        
                        # 새 글 여부 (new 이미지 존재 여부)
                        is_new = bool(row.select_one('.title img[alt="새글"]'))
                        
                        # 첨부파일 여부
                        has_attachment = bool(row.select_one('.title img[alt="첨부파일"]'))
                        
                        # 공지사항 정보를 딕셔너리로 구성
                        notice_info = {
                            'num': num,
                            'title': title,
                            'link': link,
                            'author': author,
                            'date': date,
                            'views': views,
                            'is_notice': is_notice,
                            'is_new': is_new,
                            'has_attachment': has_attachment
                        }
                        
                        all_notices.append(notice_info)
                        
                    except Exception as e:
                        logger.error(f"공지사항 행 처리 중 오류 발생: {e}")
                
                # 페이지 간 간격 두기
                if page < max_pages:
                    time.sleep(1)
            
            # 결과 저장
            self._save_notices(all_notices)
            
            return all_notices
            
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")
            return []
    
    def crawl_notice_detail(self, notice_url):
        """
        공지사항 상세 내용을 크롤링합니다.
        
        Args:
            notice_url (str): 공지사항 상세 페이지 URL
            
        Returns:
            dict: 공지사항 상세 정보
        """
        try:
            # 페이지 요청
            response = requests.get(notice_url, headers=self.headers)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 상세 내용 추출
            content_div = soup.select_one('.board_view_con')
            content = content_div.get_text(strip=True) if content_div else ""
            
            # HTML 내용 (이미지 등 포함)
            content_html = str(content_div) if content_div else ""
            
            # 첨부파일 추출
            attachments = []
            attachment_list = soup.select('.board_view_file li')
            
            for attachment in attachment_list:
                link_tag = attachment.select_one('a')
                if link_tag and 'href' in link_tag.attrs:
                    file_name = link_tag.get_text(strip=True)
                    file_url = self.base_url + link_tag['href']
                    attachments.append({
                        'name': file_name,
                        'url': file_url
                    })
            
            # 결과 반환
            detail_info = {
                'content': content,
                'content_html': content_html,
                'attachments': attachments
            }
            
            return detail_info
            
        except Exception as e:
            logger.error(f"상세 내용 크롤링 중 오류 발생: {e}")
            return {
                'content': "",
                'content_html': "",
                'attachments': []
            }
    
    def _save_notices(self, notices):
        """
        크롤링한 공지사항을 JSON 파일로 저장합니다.
        
        Args:
            notices (list): 공지사항 목록
        """
        try:
            file_path = os.path.join(self.data_dir, 'notices.json')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notices, f, ensure_ascii=False, indent=2)
                
            logger.info(f"공지사항 {len(notices)}건이 {file_path}에 저장되었습니다.")
            
        except Exception as e:
            logger.error(f"공지사항 저장 중 오류 발생: {e}")
    
    def load_notices(self):
        """
        저장된 공지사항을 로드합니다.
        
        Returns:
            list: 공지사항 목록
        """
        try:
            file_path = os.path.join(self.data_dir, 'notices.json')
            
            if not os.path.exists(file_path):
                logger.warning(f"저장된 공지사항 파일이 없습니다: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                notices = json.load(f)
                
            logger.info(f"공지사항 {len(notices)}건을 로드했습니다.")
            return notices
            
        except Exception as e:
            logger.error(f"공지사항 로드 중 오류 발생: {e}")
            return []

# 테스트 코드
if __name__ == "__main__":
    crawler = DongseoNoticeCrawler()
    notices = crawler.crawl_notices(max_pages=2)
    print(f"크롤링된 공지사항: {len(notices)}건")
    
    if notices:
        # 첫 번째 공지사항 상세 내용 크롤링
        detail = crawler.crawl_notice_detail(notices[0]['link'])
        print(f"첫 번째 공지사항 내용 길이: {len(detail['content'])}")
        print(f"첨부파일 수: {len(detail['attachments'])}")
