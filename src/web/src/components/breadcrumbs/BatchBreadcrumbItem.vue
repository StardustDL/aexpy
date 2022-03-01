<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { BatchIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

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
</template>