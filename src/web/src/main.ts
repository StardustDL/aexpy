import { createApp } from 'vue'
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'

import { store, key } from './services/store'

import App from './App.vue'
import Home from './pages/Home.vue'
import PreprocessIndex from './pages/preprocessing/Index.vue'
import PreprocessView from './pages/preprocessing/View.vue'
import ExtractIndex from './pages/extracting/Index.vue'
import ExtractView from './pages/extracting/View.vue'
import DiffIndex from './pages/differing/Index.vue'
import DiffView from './pages/differing/View.vue'
import EvaluateIndex from './pages/evaluating/Index.vue'
import EvaluateView from './pages/evaluating/View.vue'
import ReportIndex from './pages/reporting/Index.vue'
import ReportView from './pages/reporting/View.vue'
import BatchIndex from './pages/batching/Index.vue'
import BatchView from './pages/batching/View.vue'
import CodeIndex from './pages/coding/Index.vue'
import NotFound from './pages/NotFound.vue'
import { publicModels } from './services/utils'

const routes = [
    {
        path: '/',
        component: Home,
        meta: {
            title: 'Home - Aexpy'
        }
    },
    {
        path: '/preprocessing',
        component: PreprocessIndex,
        meta: {
            title: 'Preprocessing - Aexpy'
        }
    },
    {
        path: '/preprocessing/:provider/:id',
        component: PreprocessView,
        meta: {
            title: 'Preprocessing - Aexpy'
        }
    },
    {
        path: '/extracting',
        component: ExtractIndex,
        meta: {
            title: 'Extracting - Aexpy'
        }
    },
    {
        path: '/extracting/:provider/:id',
        component: ExtractView,
        meta: {
            title: 'Extracting - Aexpy'
        }
    },
    {
        path: '/differing',
        component: DiffIndex,
        meta: {
            title: 'Differing - Aexpy'
        }
    },
    {
        path: '/differing/:provider/:id',
        component: DiffView,
        meta: {
            title: 'Differing - Aexpy'
        }
    },
    {
        path: '/evaluating',
        component: EvaluateIndex,
        meta: {
            title: 'Evaluating - Aexpy'
        }
    },
    {
        path: '/evaluating/:provider/:id',
        component: EvaluateView,
        meta: {
            title: 'Evaluating - Aexpy'
        }
    },
    {
        path: '/reporting',
        component: ReportIndex,
        meta: {
            title: 'Reporting - Aexpy'
        }
    },
    {
        path: '/reporting/:provider/:id',
        component: ReportView,
        meta: {
            title: 'Reporting - Aexpy'
        }
    },
    {
        path: '/batching',
        component: BatchIndex,
        meta: {
            title: 'Batching - Aexpy'
        }
    },
    {
        path: '/batching/:provider/:id',
        component: BatchView,
        meta: {
            title: 'Batching - Aexpy'
        }
    },
    {
        path: '/coding',
        component: CodeIndex,
        meta: {
            title: 'Coding - Aexpy'
        }
    },
    // {
    //     path: '/:id',
    //     component: MaterialView,
    //     meta: {
    //         title: 'Loading... - Aexpy'
    //     }
    // },
    // {
    //     path: '/:id/:noteId',
    //     component: NoteView,
    //     meta: {
    //         title: 'Loading... - Loading... - Aexpy'
    //     }
    // },
    {
        path: '/:path*',
        component: NotFound,
        meta: {
            title: 'Not found - Aexpy'
        }
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes: routes,
})

router.beforeEach((to, from) => {
    if (to.path == from.path) {
        return true;
    }
    document.title = (to.meta.title as any).toString();
    return true;
});

const app = createApp(App);
app.use(router).use(store, key);

app.mount('#app')

publicModels();
