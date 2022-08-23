<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { DiffIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const store = useStore();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/diff">
            <n-icon>
                <DiffIcon />
            </n-icon>
            Diff
        </router-link>
    </n-breadcrumb-item>
</template>