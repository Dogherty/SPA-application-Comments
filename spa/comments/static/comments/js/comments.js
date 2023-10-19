function getCsrfToken() {
  const csrfTokenCookie = document.cookie
    .split('; ')
    .find(cookie => cookie.startsWith("csrftoken="));

  if (csrfTokenCookie) {
    return csrfTokenCookie.split("=")[1];
  }
  return null;
}

axios.interceptors.request.use(config => {
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

const Comment = {
  template: `
  <div class="comment-block">
  <div class="comment">
  <header>
  <div class="user-info">
      <span class="user-name">{{ comment.user_name }}</span>
      <span class="comment-date">{{ comment.created_at }}</span>
    </div>
    </header>
  <div class="comment-text" v-html="comment.text">
  </div>
    <div v-if="comment.text_file">
    <p>Текстовый файл: {{ getFileName(comment.text_file) }}
      <a :href="comment.text_file" download>Скачать</a>
    </p>
    </div>
    <div v-if="comment.image">
      <img :src="comment.image" alt="Image" @mouseover="imageHover(true)" @mouseout="imageHover(false)">
    </div>
    <button class="reply" @click="showReplyForm(comment)">Reply</button>
    <div v-if="replyToCommentId === comment.id">
    <section class="comment-form slide-in" id="ugcNewComment">
    <h3 class="section-title">Оставьте ваш комментарий</h3>
    <form @submit.prevent="submitComment(year, month, day, postID)">
      {{ comment_form.non_field_errors }}
      <div class="form-group">
        <div class="form-field">
          <label for="user_name">Имя:</label>
          <input v-model="commentForm.user_name" type="text" id="user_name" class="form-control" placeholder="Ваше имя">
        </div>
        <div class="form-field">
          <label for="home_page">Сайт:</label>
          <input v-model="commentForm.home_page" type="text" id="home_page" class="form-control" placeholder="Ваш сайт">
        </div>
        <div class="form-field">
          <label for="email">E-mail:</label>
          <input v-model="commentForm.email" type="text" id="email" class="form-control" placeholder="youremail@example.com">
        </div>
        
        <div class="form-field">
          <label for="text">Текст:</label>
          <div class="tag-buttons">
            <button type="button" @click="insertTag('[i]')">[i]</button>
            <button type="button" @click="insertTag('[strong]')">[strong]</button>
            <button type="button" @click="insertTag('[code]')">[code]</button>
            <button type="button" @click="insertTag('[a]')">[a]</button>
          </div>
          <textarea v-model="commentForm.text" id="text" class="form-control" rows="6" cols="20" placeholder="Ваш комментарий"></textarea>
        </div>
        <div class="form-file">
          <label for="image">Загрузить фото:</label>
          <input type="file" id="image" class="custom-file-input" @change="handleImageUpload">
        </div>
        <div class="form-file">
          <label for="image">Загрузить TXT-файл:</label>
          <input type="file" id="image" class="custom-file-input" @change="handleFileUpload">
        </div>
        <div class="form-field">
          <label for="captcha">Captcha:</label>
        </div>
        <div class="form-captcha-image">
          <img v-if="commentForm.captcha" :src="commentForm.captcha.image_url" alt="Captcha">
          <button class="captcha-button" type="button" @click="getCaptcha()">Обновить</button>
        </div>
        <div class="form-field">
          <input v-model="commentForm.captcha.value" type="text" id="captcha" class="form-control" placeholder="Введите код с изображения">
        </div>
      </div>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <button type="submit">Отправить</button>
    </form>
  </section>
  
      </div>
    </div>
    <div v-if="comment.children.length > 0">
      <ul>
        <li v-for="child_comment in comment.children">
          <comment :comment="child_comment" :comment_form="comment_form" :show-comment-form="showCommentForm" />
        </li>
      </ul>
    </div>
    </div>
  `,
  props: ['comment', 'comment_form', 'showCommentForm'],
  data() {
    return {
      i: 1,
      replyToCommentId: null,
      commentForm: {
        user_name: '',
        email: '',
        home_page: '',
        captcha: '',
        text: '',
        image: null,
        file: null,
      },
      errorMessage: '',
      year: null,
      month: null,
      day: null,
      postID: null,
    };
  },
  methods: {
    getCaptcha() {
      axios.get('/get_captcha/')
          .then(response => {
            this.commentForm.captcha = response.data;
          })
          .catch(error => {
            console.error('Ошибка при получении капчи:', error);
          });
    },
    updateComments() {
      this.$root.updateComments();
    },
    imageHover(shouldEnlarge) {
      const imageElement = document.querySelector('.comment img');
      if (shouldEnlarge) {
        imageElement.style.transform = 'scale(1.1)';
      } else {
        imageElement.style.transform = 'scale(1)';
      }
    },
    sanitizeHTML(html) {
      return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['a', 'code', 'i', 'strong'],
        ALLOWED_ATTR: ['href', 'title'],
      });
    },
    insertTag(tag) {
      const textArea = document.getElementById('text');
      const start = textArea.selectionStart;
      const end = textArea.selectionEnd;
      const text = this.commentForm.text;
      const textBeforeSelection = text.slice(0, start);
      const selectedText = text.slice(start, end);
      const textAfterSelection = text.slice(end);
  
      this.commentForm.text = textBeforeSelection + `<${tag.slice(1, -1)}>${selectedText}</${tag.slice(1, -1)}>` + textAfterSelection;
      textArea.selectionStart = start + tag.length + selectedText.length * 2;
      textArea.selectionEnd = textArea.selectionStart;
    },
    getFileName(filePath) {
      return filePath.split('/').pop();
    },
    showReplyForm(comment) {
      if (this.replyToCommentId === comment.id) {
        this.replyToCommentId = null;
      } else {
        this.replyToCommentId = comment.id;
        if (!this.commentForm) {
          this.commentForm = {};
        }
        this.getCaptcha();
      }
    },
    handleImageUpload(event) {
      this.commentForm.image = event.target.files[0];
    },
    handleFileUpload(event) {
      this.commentForm.file = event.target.files[0];
    },
    submitComment() {
      const postID = document.getElementById('app').getAttribute('data-post-id');
      const year = document.getElementById('app').getAttribute('data-year');
      const month = document.getElementById('app').getAttribute('data-month');
      const day = document.getElementById('app').getAttribute('data-day');

      let formData = new FormData();
      formData.append('user_name', this.commentForm.user_name);
      formData.append('email', this.commentForm.email);
      formData.append('home_page', this.commentForm.home_page);
      formData.append('text', this.sanitizeHTML(this.commentForm.text));
      formData.append('captcha_value', this.commentForm.captcha.value);
      formData.append('captcha_key', this.commentForm.captcha.key);
      formData.append('image', this.commentForm.image);
      formData.append('file', this.commentForm.file);
      formData.append('parent_comment', this.replyToCommentId);
    
      const postURL = `/api/v1/comments/${year}/${month}/${day}/${postID}/create/`;
      let config = {
        header : {
         'Content-Type' : 'multipart/form-data'
       }
      }
      axios.post(postURL, formData, config)
        .then(response => {
          this.replyToCommentId = null;
          this.updateComments()
        })
        .catch(error => {
          this.getCaptcha();
          if (error.response && error.response.data) {
            this.errorMessage = error.response.data.message;
          } else {
            this.errorMessage = 'Произошла ошибка при отправке комментария.';
          }
          console.error('Ошибка при отправке комментария:', error);
        });
    },
  },
};



Vue.component('comment', Comment);

new Vue({
  el: '#app',
  data: {
    test: 'ddddddddd',
    page: 1,
    total_pages: 1,
    post: null,
    comments: null,
    commentComponent: 'comment',
    showForm: false,
    commentForm: {
      user_name: '',
      email: '',
      home_page: '',
      captcha: '',
      text: '',
      image: null,
      file: null,
      csrf_token: '',
      sort_by: '',
      order: 'asc',
    },
    errorMessage: '',
    year: null,
    month: null,
    day: null,
    postID: null,
    comment_form: {},
    sortButtonTexts: {
      'user_name': 'Имени',
      'email': 'E-mail',
      'date_added': 'Дате'
  },

  },
  methods: {
    getCaptcha() {
      axios.get('/get_captcha/')
          .then(response => {
            this.commentForm.captcha = response.data;
          })
          .catch(error => {
            console.error('Ошибка при получении капчи:', error);
          });
    },
    updateComments() {
      const postID = document.getElementById('app').getAttribute('data-post-id');
      const year = document.getElementById('app').getAttribute('data-year');
      const month = document.getElementById('app').getAttribute('data-month');
      const day = document.getElementById('app').getAttribute('data-day');
      const postURL = `/api/v1/comments/${year}/${month}/${day}/${postID}/`;

      if (postURL) {
        axios.get(postURL)
          .then(response => {
            this.post = response.data.post;
            this.comments = response.data.comments;
          })
          .catch(error => {
            console.error('Ошибка при загрузке данных:', error);
          });
      }
    },
    sanitizeHTML(html) {
      return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['a', 'code', 'i', 'strong'],
        ALLOWED_ATTR: ['href', 'title'],
      });
    },
    insertTag(tag) {
      const textArea = document.getElementById('text');
      const start = textArea.selectionStart;
      const end = textArea.selectionEnd;
      const text = this.commentForm.text;
      const textBeforeSelection = text.slice(0, start);
      const selectedText = text.slice(start, end);
      const textAfterSelection = text.slice(end);
  
      this.commentForm.text = textBeforeSelection + `<${tag.slice(1, -1)}>${selectedText}</${tag.slice(1, -1)}>` + textAfterSelection;
      textArea.selectionStart = start + tag.length + selectedText.length * 2;
      textArea.selectionEnd = textArea.selectionStart;
    },
    loadPage(page) {
      const postID = document.getElementById('app').getAttribute('data-post-id');
      const year = document.getElementById('app').getAttribute('data-year');
      const month = document.getElementById('app').getAttribute('data-month');
      const day = document.getElementById('app').getAttribute('data-day');
      let sort_by = this.comment_form.sort_by;
      let order = this.comment_form.order;
      let postURL = `/api/v1/comments/${year}/${month}/${day}/${postID}/?page=${page}`;
      if (sort_by) {
        postURL += `&sort_by=${sort_by}&order=${order}`;
      }
      if (postURL) {
        axios.get(postURL)
          .then(response => {
            this.post = response.data.post;
            this.comments = response.data.comments;
            this.page = response.data.page;
            this.total_pages = response.data.total_pages;
          })
          .catch(error => {
            console.error('Ошибка при загрузке данных:', error);
          });
      }
    },
    sortComments(sortBy) {
      const postID = document.getElementById('app').getAttribute('data-post-id');
      const year = document.getElementById('app').getAttribute('data-year');
      const month = document.getElementById('app').getAttribute('data-month');
      const day = document.getElementById('app').getAttribute('data-day');
      let currentSortBy = sortBy;
      let currentOrder = 'asc';
  
      if (this.comment_form.sort_by === sortBy) {
        currentOrder = this.comment_form.order === 'asc' ? 'desc' : 'asc';
      }
  
      this.comment_form.sort_by = currentSortBy;
      this.comment_form.order = currentOrder;
      
      const postURL = `/api/v1/comments/${year}/${month}/${day}/${postID}/?sort_by=${currentSortBy}&order=${currentOrder}`;

      if (postURL) {
          axios.get(postURL)
              .then(response => {
                  this.post = response.data.post;
                  this.comments = response.data.comments;
              })
              .catch(error => {
                  console.error('Ошибка при загрузке данных:', error);
              });
      }
      const button = event.target;
      button.textContent = `${this.sortButtonTexts[currentSortBy]} (${currentOrder === 'asc' ? '↑' : '↓'})`;
  },
    handleImageUpload(event) {
      this.commentForm.image = event.target.files[0];
    },
    handleFileUpload(event) {
      this.commentForm.file = event.target.files[0];
    },
    showCommentForm() {
      if (this.showForm){
        this.showForm = false;
      }
      else{
        this.showForm = true;
        this.getCaptcha();
      }
    },
    submitComment() {
      const postID = document.getElementById('app').getAttribute('data-post-id');
      const year = document.getElementById('app').getAttribute('data-year');
      const month = document.getElementById('app').getAttribute('data-month');
      const day = document.getElementById('app').getAttribute('data-day');
    
      let formData = new FormData();
      formData.append('user_name', this.commentForm.user_name);
      formData.append('email', this.commentForm.email);
      formData.append('home_page', this.commentForm.home_page);
      formData.append('text', this.sanitizeHTML(this.commentForm.text));
      formData.append('captcha_value', this.commentForm.captcha.value);
      formData.append('captcha_key', this.commentForm.captcha.key);
      formData.append('image', this.commentForm.image);
      formData.append('file', this.commentForm.file);
    
      const postURL = `/api/v1/comments/${year}/${month}/${day}/${postID}/create/`;
      let config = {
        header : {
         'Content-Type' : 'multipart/form-data'
       }
      }
      axios.post(postURL, formData, config)
        .then(response => {
          this.showForm = false;
          this.updateComments();
        })
        .catch(error => {
          this.getCaptcha();
          if (error.response && error.response.data) {
            this.errorMessage = error.response.data.message;
          } else {
            this.errorMessage = 'Произошла ошибка при отправке комментария.';
          }
          console.error('Ошибка при отправке комментария:', error);
        });
    },
    
  },
  created() {
    this.updateComments();
    this.loadPage(1);
  },
});