import { createApp } from 'vue'
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import VNetworkGraph from "v-network-graph"
import "v-network-graph/lib/style.css"
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
            title: 'Home'
        }
    },
    {
        path: '/preprocessing',
        component: PreprocessIndex,
        meta: {
            title: 'Preprocessing'
        }
    },
    {
        path: '/preprocessing/:pipeline/:id',
        component: PreprocessView,
        meta: {
            title: 'Preprocessing'
        }
    },
    {
        path: '/extracting',
        component: ExtractIndex,
        meta: {
            title: 'Extracting'
        }
    },
    {
        path: '/extracting/:pipeline/:id',
        component: ExtractView,
        meta: {
            title: 'Extracting'
        }
    },
    {
        path: '/differing',
        component: DiffIndex,
        meta: {
            title: 'Differing'
        }
    },
    {
        path: '/differing/:pipeline/:id',
        component: DiffView,
        meta: {
            title: 'Differing'
        }
    },
    {
        path: '/reporting',
        component: ReportIndex,
        meta: {
            title: 'Reporting'
        }
    },
    {
        path: '/reporting/:pipeline/:id',
        component: ReportView,
        meta: {
            title: 'Reporting'
        }
    },
    {
        path: '/batching',
        component: BatchIndex,
        meta: {
            title: 'Batching - AexPy'
        }
    },
    {
        path: '/batching/:pipeline/:id',
        component: BatchView,
        meta: {
            title: 'Batching - AexPy'
        }
    },
    {
        path: '/coding',
        component: CodeIndex,
        meta: {
            title: 'Coding - AexPy'
        }
    },
    // {
    //     path: '/:id',
    //     component: MaterialView,
    //     meta: {
    //         title: 'Loading... - AexPy'
    //     }
    // },
    // {
    //     path: '/:id/:noteId',
    //     component: NoteView,
    //     meta: {
    //         title: 'Loading... - Loading... - AexPy'
    //     }
    // },
    {
        path: '/:path*',
        component: NotFound,
        meta: {
            title: 'Not Found'
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
    let params = <{
        pipeline?: string,
        id?: string,
    }>to.params;
    let title = (to.meta.title as any).toString() + " - AexPy";
    if (params.pipeline) {
        title = `${params.pipeline} - ${title}`;
    }
    if (params.id) {
        title = `${params.id} - ${title}`;
    }
    document.title = title;
    return true;
});

const app = createApp(App);
app.use(router).use(store, key).use(VNetworkGraph);

app.mount('#app')

publicModels();
