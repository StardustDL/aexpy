<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { ExtractIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const store = useStore();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/extract">
            <n-icon>
                <ExtractIcon />
            </n-icon>
            Extract
        </router-link>
    </n-breadcrumb-item>
</template>