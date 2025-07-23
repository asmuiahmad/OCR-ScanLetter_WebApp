from flask import Blueprint, render_template

pagination_demo_bp = Blueprint('pagination_demo', __name__)

class MockPagination:
    def __init__(self, page, pages, total, has_prev=False, has_next=False, prev_num=None, next_num=None):
        self.page = page
        self.pages = pages
        self.total = total
        self.has_prev = has_prev
        self.has_next = has_next
        self.prev_num = prev_num
        self.next_num = next_num
    
    def iter_pages(self, left_edge=1, right_edge=1, left_current=1, right_current=2):
        """Generate page numbers for pagination"""
        last = self.pages
        for num in range(1, last + 1):
            if num <= left_edge or \
               (self.page - left_current - 1 < num < self.page + right_current) or \
               num > last - right_edge:
                yield num

@pagination_demo_bp.route('/pagination-demo')
def pagination_demo():
    # Create mock pagination objects for demonstration
    single_page_pagination = MockPagination(page=1, pages=1, total=5)
    
    first_page_pagination = MockPagination(
        page=1, pages=10, total=100, 
        has_prev=False, has_next=True, 
        prev_num=None, next_num=2
    )
    
    middle_page_pagination = MockPagination(
        page=5, pages=10, total=100, 
        has_prev=True, has_next=True, 
        prev_num=4, next_num=6
    )
    
    last_page_pagination = MockPagination(
        page=10, pages=10, total=100, 
        has_prev=True, has_next=False, 
        prev_num=9, next_num=None
    )
    
    return render_template('examples/pagination_demo.html',
                         single_page_pagination=single_page_pagination,
                         first_page_pagination=first_page_pagination,
                         middle_page_pagination=middle_page_pagination,
                         last_page_pagination=last_page_pagination)