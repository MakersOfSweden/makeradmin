<?php

use Illuminate\Support\Facades\Schema;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Database\Migrations\Migration;

class CreateMembershipMembersTable extends Migration
{
	/**
	 * Run the migrations.
	 *
	 * @return void
	 */
	public function up()
	{
		Schema::create("membership_members", function (Blueprint $table)
		{
			$table->increments("member_id");
			$table->string("email");
			$table->string("password", 60)->nullable();
			$table->string("firstname");
			$table->string("lastname");
			$table->string("civicregno", 12)->nullable();
			$table->string("company")->nullable();
			$table->string("orgno", 12)->nullable();
			$table->string("address_street")->nullable();
			$table->string("address_extra")->nullable();
			$table->integer("address_zipcode")->nullable();
			$table->string("address_city")->nullable();
			$table->string("address_country", 2)->nullable();
			$table->string("phone")->nullable();
			$table->timestamps();
			$table->softDeletes();

			$table->index("email");
		});
	}

	/**
	 * Reverse the migrations.
	 *
	 * @return void
	 */
	public function down()
	{
		Schema::drop("membership_members");
	}
}