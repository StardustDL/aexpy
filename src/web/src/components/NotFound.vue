<script setup lang="ts">
import { NButton, NIcon, NResult } from 'naive-ui'
import { AlertCircle } from '@vicons/tabler'
import { HomeIcon } from './icons'
import { RouterLink } from 'vue-router'

defineProps<{
    path: string,
    home?: boolean
}>();

</script>

<script lang="ts">
export default {
    components: {
        HomeIcon,
        AlertCircle,
    }
}
</script>

<template>
    <n-result
        :status="'404'"
        title="Not Found"
        :description="`Path: ${path}`"
        style="margin: 50px;"
    >
        <template #footer>
            <n-button v-if="home != false">
                <template #icon>
                    <n-icon>
                        <HomeIcon />
                    </n-icon>
                </template>
                <router-link to="/">Home</router-link>
            </n-button>
        </template>
    </n-result>
</template>

<style scoped>
a {
    text-decoration: none;
    color: inherit;
}
</style>