export default function Placeholder({ name }) {
  return (
    <div style={{ opacity: 0.4, marginTop: '4rem', textAlign: 'center' }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚧</div>
      <p style={{ fontSize: '1.1rem' }}>{name} — próximamente</p>
    </div>
  )
}
