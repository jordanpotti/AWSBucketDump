rule pdf_file
{
	strings:
		$magic = { 25 50 44 46 }
		
	condition:
		$magic at 0
}
