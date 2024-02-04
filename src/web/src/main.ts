import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { store, key } from './services/store'

import App from './App.vue'
import Home from './pages/Home.vue'
import DistributionView from './pages/view/Distribution.vue'
import DescriptionView from './pages/view/Description.vue'
import DifferenceView from './pages/view/Difference.vue'
import ReportView from './pages/view/Report.vue'
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
        path: '/distribution',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/description',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/difference',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/report',
        component: Home,
        meta: {
            title: 'Home'
        }
    },
    {
        path: '/distribution/:id',
        component: DistributionView,
        meta: {
            title: 'Distribution'
        }
    },
    {
        path: '/description/:id',
        component: DescriptionView,
        meta: {
            title: 'Description'
        }
    },
    {
        path: '/difference/:id',
        component: DifferenceView,
        meta: {
            title: 'Difference'
        }
    },
    {
        path: '/report/:id',
        component: ReportView,
        meta: {
            title: 'Report'
        }
    },
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
        id?: string,
    }>to.params;
    let title = (to.meta.title as any).toString() + " - AexPy";
    if (params.id) {
        title = `${params.id} - ${title}`;
    }
    document.title = title;
    return true;
});

const app = createApp(App);
app.use(router).use(store, key);

app.mount('#app')

publicModels();
