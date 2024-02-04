<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { ExtractIcon } from '../icons'
import { RouterLink } from 'vue-router'
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/description">
            <n-icon>
                <ExtractIcon />
            </n-icon>
            Description
        </router-link>
    </n-breadcrumb-item>
</template>