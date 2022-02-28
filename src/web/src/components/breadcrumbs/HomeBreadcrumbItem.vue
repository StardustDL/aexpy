<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { HomeIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const store = useStore();
const title = await store.state.api.title();
</script>

<script lang="ts">
export default {
    components: {
        HomeIcon,
    }
}
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/">
            <n-icon>
                <HomeIcon />
            </n-icon>
            {{ title }}
        </router-link>
    </n-breadcrumb-item>
</template>