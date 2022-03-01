<script setup lang="ts">
import { NIcon, NBreadcrumbItem } from 'naive-ui'
import { EvaluateIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'

const store = useStore();
</script>

<template>
    <n-breadcrumb-item>
        <router-link to="/evaluating">
            <n-icon>
                <EvaluateIcon />
            </n-icon>
            Evaluate
        </router-link>
    </n-breadcrumb-item>
</template>