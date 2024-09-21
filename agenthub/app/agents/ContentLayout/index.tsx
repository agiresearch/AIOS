import DatasetsList from './DatasetsList'

export default function ContentLayout({ searchParams }:
  { searchParams: { [key: string]: string | string[] | undefined } }) {
  return <DatasetsList searchParams={searchParams} />
}