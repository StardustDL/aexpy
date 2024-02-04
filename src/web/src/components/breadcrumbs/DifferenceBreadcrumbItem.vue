<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { DiffIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/difference">
            <n-icon>
                <DiffIcon />
            </n-icon>
            Difference
        </router-link>
    </n-breadcrumb-item>
</template>