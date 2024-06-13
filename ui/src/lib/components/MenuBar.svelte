<script lang="ts">
	export let title: string = 'Menu';
</script>

<div class="top-menu">
	{title}
</div>

<style>
	.top-menu {
		width: 100%;
		height: 100px;
		background-color: #333;
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		position: fixed;
		top: 0;
		font-family: 'Roboto', sans-serif;
	}
</style>
