<script setup lang="ts">
import { NButton, NIcon, NResult } from 'naive-ui'
import { AlertCircle } from '@vicons/tabler'
import { HomeIcon } from './icons'
import { RouterLink } from 'vue-router'

defineProps<{
    path?: string,
    home?: boolean,
    size?: "small" | "medium" | "large" | "huge",
}>();

</script>

<template>
    <n-result :status="'404'" title="Not Found" :description="`Path: ${path ?? '/'}`" style="margin: 50px;" :size="size">
        <template #footer>
            <router-link to="/" custom v-slot="{ href, navigate }" v-if="home">
                <n-button :href="href" @click="navigate">
                    <template #icon>
                        <n-icon :component="HomeIcon" />
                    </template>
                    Home
                </n-button>
            </router-link>
        </template>
    </n-result>
</template>

<style scoped>
a {
    text-decoration: none;
    color: inherit;
}
</style>