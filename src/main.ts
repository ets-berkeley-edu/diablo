import Vue from 'vue';

Vue.config.productionTip = false;

// Emit, and listen for, events via hub
Vue.prototype.$eventHub = new Vue();
