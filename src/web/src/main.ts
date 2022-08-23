import { createApp } from 'vue'
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import VNetworkGraph from "v-network-graph"
import "v-network-graph/lib/style.css"
import { store, key } from './services/store'

import App from './App.vue'
import Home from './pages/Home.vue'
import PreprocessIndex from './pages/preprocess/Index.vue'
import PreprocessView from './pages/preprocess/View.vue'
import ExtractIndex from './pages/extract/Index.vue'
import ExtractView from './pages/extract/View.vue'
import DiffIndex from './pages/diff/Index.vue'
import DiffView from './pages/diff/View.vue'
import EvaluateIndex from './pages/evaluating/Index.vue'
import EvaluateView from './pages/evaluating/View.vue'
import ReportIndex from './pages/report/Index.vue'
import ReportView from './pages/report/View.vue'
import BatchIndex from './pages/batch/Index.vue'
import BatchView from './pages/batch/View.vue'
import CodeIndex from './pages/code/Index.vue'
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
        path: '/preprocess',
        component: PreprocessIndex,
        meta: {
            title: 'Preprocess'
        }
    },
    {
        path: '/preprocess/:pipeline/:id',
        component: PreprocessView,
        meta: {
            title: 'Preprocess'
        }
    },
    {
        path: '/extract',
        component: ExtractIndex,
        meta: {
            title: 'Extract'
        }
    },
    {
        path: '/extract/:pipeline/:id',
        component: ExtractView,
        meta: {
            title: 'Extract'
        }
    },
    {
        path: '/diff',
        component: DiffIndex,
        meta: {
            title: 'Diff'
        }
    },
    {
        path: '/diff/:pipeline/:id',
        component: DiffView,
        meta: {
            title: 'Diff'
        }
    },
    {
        path: '/report',
        component: ReportIndex,
        meta: {
            title: 'Report'
        }
    },
    {
        path: '/report/:pipeline/:id',
        component: ReportView,
        meta: {
            title: 'Report'
        }
    },
    {
        path: '/batch',
        component: BatchIndex,
        meta: {
            title: 'Batch - AexPy'
        }
    },
    {
        path: '/batch/:pipeline/:id',
        component: BatchView,
        meta: {
            title: 'Batch - AexPy'
        }
    },
    {
        path: '/code',
        component: CodeIndex,
        meta: {
            title: 'Code - AexPy'
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
