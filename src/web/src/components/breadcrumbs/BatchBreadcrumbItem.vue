<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { BatchIcon, BatchIndexIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const props = defineProps<{
    isIndex?: boolean;
}>();

const store = useStore();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/batching">
            <n-icon>
                <BatchIcon />
            </n-icon>
            Batch
        </router-link>
    </n-breadcrumb-item>
    <n-breadcrumb-item v-if="isIndex">
        <router-link to="/batching">
            <n-icon>
                <BatchIndexIcon />
            </n-icon>
            Index
        </router-link>
    </n-breadcrumb-item>
</template>