/** Shows a loading or error message instead of children until data is ready. */
export default function StatusBlock({ loading, error, children }) {
  if (error) {
    return (
      <div className="status status-error" role="alert">
        <strong>Something went wrong.</strong> {error}
      </div>
    );
  }
  if (loading) {
    return (
      <div className="status" aria-busy="true">
        Loading...
      </div>
    );
  }
  return children;
}
